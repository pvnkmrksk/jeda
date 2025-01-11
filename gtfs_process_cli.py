#!/usr/bin/env python3

import argparse
import os
import sys
import shutil
import partridge as ptg
import folium
import random
from pathlib import Path
from typing import Union, List
import matplotlib.pyplot as plt
import numpy as np

# Import functions from existing files
from zip_filter_cli import (
    extract_zip,
    filter_trips,
    filter_stop_times,
    create_new_zip
)



def create_gtfs_subset(feed_path: str, target_stop_id: Union[str, List[str]], output_path: str, 
                      min_daily_trips: int = 5, only_important_stops: bool = False):
    """Create GTFS subsets for one or more target stops."""
    
    # Define output paths
    output_dir = os.path.dirname(output_path)
    base_name = os.path.splitext(os.path.basename(output_path))[0]
    full_output = os.path.join(output_dir, f"{base_name}_full.zip")
    important_output = output_path  # This is the final output file
    
    # Convert single stop ID to list for consistent processing
    target_stops = [target_stop_id] if isinstance(target_stop_id, str) else target_stop_id
    
    feed = ptg.load_feed(feed_path)
    
    # Get all trips through any of the target stops
    stop_times_at_targets = feed.stop_times[feed.stop_times['stop_id'].isin(target_stops)]
    
    # Get frequent routes
    route_trip_counts = (
        stop_times_at_targets
        .merge(feed.trips[['trip_id', 'route_id', 'service_id']], on='trip_id')
        .groupby(['route_id', 'service_id'])['trip_id']
        .nunique()
        .reset_index()
        .groupby('route_id')['trip_id']
        .max()
    )
    
    frequent_routes = route_trip_counts[route_trip_counts >= min_daily_trips].index
    
    # Get trips from frequent routes that serve any of the target stops
    frequent_trips = (
        feed.trips[feed.trips['route_id'].isin(frequent_routes)]
        .merge(stop_times_at_targets[['trip_id']], on='trip_id')
        ['trip_id']
        .unique()
    )
    
    try:
        # Create full subset first
        view_full = {'trips.txt': {'trip_id': frequent_trips}}
        ptg.extract_feed(feed_path, full_output, view_full)
        full_feed = ptg.load_feed(full_output)
        
        # Find junction stops using the full feed
        junction_stops, segments = find_true_junctions(full_feed)
        
        # Find terminal stops
        terminal_stops = set()
        for trip_id in full_feed.stop_times['trip_id'].unique():
            trip_stops = (
                full_feed.stop_times[full_feed.stop_times['trip_id'] == trip_id]
                .sort_values('stop_sequence')['stop_id']
            )
            terminal_stops.add(trip_stops.iloc[0])
            terminal_stops.add(trip_stops.iloc[-1])
        
        # Always include the target stops in the important stops
        important_stops = junction_stops | terminal_stops | set(target_stops)
        
        # Create important-stops subset if requested
        if only_important_stops:
            important_stop_times = full_feed.stop_times[
                full_feed.stop_times['stop_id'].isin(important_stops)
            ]
            
            view_important = {
                'trips.txt': {'trip_id': frequent_trips},
                'stops.txt': {'stop_id': list(important_stops)},
                'stop_times.txt': {
                    'trip_id': important_stop_times['trip_id'].unique(),
                    'stop_id': list(important_stops)
                }
            }
            
            ptg.extract_feed(feed_path, important_output, view_important)
            important_feed = ptg.load_feed(important_output)
        else:
            important_feed = full_feed
            os.replace(full_output, important_output)
        
        return {
            'full': {
                'feed': full_feed,
                'view': view_full,
                'path': full_output
            },
            'important': {
                'feed': important_feed,
                'view': view_important if only_important_stops else view_full,
                'path': important_output
            },
            'stops': {
                'junction': junction_stops,
                'terminal': terminal_stops,
                'target': set(target_stops)
            }
        }
            
    finally:
        # Clean up temporary files if needed
        if os.path.exists(full_output) and only_important_stops:
            os.remove(full_output)


def find_true_junctions(feed, similarity_threshold=0.8):
    """Find true junction stops by analyzing route patterns through sequential stops."""
    stop_times = feed.stop_times
    trips = feed.trips
    
    # Get routes through each stop
    stop_routes = (
        stop_times
        .merge(trips[['trip_id', 'route_id']], on='trip_id')
        .groupby('stop_id')
        .agg({'route_id': lambda x: set(x)})
    )
    
    # Build adjacency dictionary
    adjacency = {}
    for trip_id in stop_times['trip_id'].unique():
        trip_stops = (
            stop_times[stop_times['trip_id'] == trip_id]
            .sort_values('stop_sequence')['stop_id']
            .tolist()
        )
        
        for i in range(len(trip_stops)-1):
            current = trip_stops[i]
            next_stop = trip_stops[i+1]
            
            if current not in adjacency:
                adjacency[current] = set()
            adjacency[current].add(next_stop)
    
    def route_similarity(stop1, stop2):
        routes1 = stop_routes.loc[stop1, 'route_id']
        routes2 = stop_routes.loc[stop2, 'route_id']
        return len(routes1.intersection(routes2)) / len(routes1.union(routes2))
    
    def find_linear_segment(stop_id, visited):
        segment = {stop_id}
        if stop_id not in adjacency:
            return segment
            
        current = stop_id
        while True:
            next_stops = adjacency.get(current, set()) - visited
            if len(next_stops) != 1:
                break
            
            next_stop = next_stops.pop()
            if route_similarity(current, next_stop) < similarity_threshold:
                break
            
            segment.add(next_stop)
            visited.add(next_stop)
            current = next_stop
        
        return segment
    
    visited = set()
    segments = []
    
    for stop_id in stop_routes.index:
        if stop_id in visited:
            continue
        
        segment = find_linear_segment(stop_id, visited)
        segments.append(segment)
        visited.update(segment)
    
    junction_stops = set()
    for i, segment in enumerate(segments):
        neighbors = set()
        for stop in segment:
            if stop in adjacency:
                neighbors.update(adjacency[stop])
        
        connecting_segments = sum(
            1 for other_seg in segments 
            if i != segments.index(other_seg) and neighbors.intersection(other_seg)
        )
        
        if connecting_segments > 1:
            junction_stops.update({min(segment), max(segment)})
    
    return junction_stops, segments

def visualize_stops(feed, stop_types, show_routes=True):
    """
    Visualize stops with different colors for junction, terminal, and intermediate stops.
    
    Args:
        feed: GTFS feed
        stop_types: dict containing 'junction' and 'terminal' stop sets
        show_routes: bool, whether to display route shapes
    """
    import folium
    import random
    import matplotlib.pyplot as plt
    
    # Create base map centered on the network
    m = folium.Map(
        location=[
            feed.stops['stop_lat'].mean(),
            feed.stops['stop_lon'].mean()
        ],
        zoom_start=12
    )
    
    junction_stops = stop_types['junction']
    terminal_stops = stop_types['terminal']
    
    # Draw routes first if requested
    if show_routes and hasattr(feed, 'shapes'):
        shape_ids = feed.trips['shape_id'].unique()
        
        # Create colormap
        cmap = plt.get_cmap('tab20c')
        # Get the number of unique routes for proper color distribution
        n_routes = len(shape_ids)
        # Create evenly spaced indices for the colormap
        color_indices = np.linspace(0, 1, n_routes)
        
        for i, shape_id in enumerate(shape_ids):
            shape_points = feed.shapes[feed.shapes['shape_id'] == shape_id]
            shape_points = shape_points.sort_values('shape_pt_sequence')
            route_coords = shape_points[['shape_pt_lat', 'shape_pt_lon']].values.tolist()
            
            # Get color from tab20c colormap using normalized index
            rgba_color = cmap(color_indices[i])
            route_color = '#{:02x}{:02x}{:02x}'.format(
                int(rgba_color[0] * 255),
                int(rgba_color[1] * 255),
                int(rgba_color[2] * 255)
            )
            

            
            # Main route line with medium opacity for better color mixing
            folium.PolyLine(
                locations=route_coords,
                weight=8,
                color=route_color,
                opacity=1  # Medium opacity for main line
            ).add_to(m)
    
    # Plot all stops with different colors based on type
    for _, stop in feed.stops.iterrows():
        stop_id = stop['stop_id']
        
        # Determine stop type and corresponding style
        if stop_id in junction_stops:
            color = 'red'
            radius = 6
            opacity = 0.9
            label = 'Junction'
        elif stop_id in terminal_stops:
            color = 'green'
            radius = 5
            opacity = 0.8
            label = 'Terminal'
        else:
            color = 'blue'
            radius = 4
            opacity = 0.6
            label = 'Intermediate'
        
        # Create popup content
        popup_content = f"""
            <b>{stop['stop_name']}</b><br>
            ID: {stop_id}<br>
            Type: {label}
        """
        
        folium.CircleMarker(
            location=[stop['stop_lat'], stop['stop_lon']],
            radius=radius,
            color=color,
            fill=True,
            popup=folium.Popup(popup_content, max_width=300),
            opacity=opacity
        ).add_to(m)
    
    # Add a legend
    legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; 
                    border:2px solid grey; z-index:9999; 
                    background-color:white;
                    padding: 10px;
                    font-size:14px;
                    ">
            <p style="margin-bottom:5px"><b>Stop Types</b></p>
            <p>
                <i class="fa fa-circle" style="color:red"></i> Junction Stops<br>
                <i class="fa fa-circle" style="color:green"></i> Terminal Stops<br>
                <i class="fa fa-circle" style="color:blue"></i> Intermediate Stops
            </p>
        </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m
def process_gtfs_complete(input_path: str, target_stops: list[str], output_dir: str="examples", 
                         min_trips: int=5, important_stops: bool=True, show_routes: bool=True,
                         skip_direction_filter: bool=False, direction_flag: int=1, 
                         output_file='subset_filtered.zip', viz_file='network_stops.html'):
    """Combined processing function that handles the entire workflow"""
    
    try:
        print(f"Processing GTFS file: {input_path}")
        print(f"Target stops: {target_stops}")
        
        os.makedirs(output_dir, exist_ok=True)
        subset_path = os.path.join(output_dir, "subset.zip")
        
        # Step 1: Create GTFS subset for multiple stops
        print("Creating GTFS subset...")
        result = create_gtfs_subset(
            feed_path=input_path,
            target_stop_id=target_stops,
            output_path=subset_path,
            min_daily_trips=min_trips,
            only_important_stops=important_stops
        )
        
        if not os.path.exists(subset_path):
            raise FileNotFoundError(f"Subset file was not created at {subset_path}")
            
        # Step 2: Create visualization if requested
        # Create visualization for all stop in one file
        viz_path = os.path.join(output_dir, f"{viz_file}")
        map_viz = visualize_stops(
            result['full']['feed'],
            result['stops'],
            show_routes=show_routes
        )
        map_viz.save(viz_path)

        print(f"Visualization saved to {viz_path}")
        if skip_direction_filter:
            # Just rename the subset file to the output file
            shutil.move(subset_path, output_file)
            return Path(output_file)
        
        # Step 3: Filter by direction (only if not skipped)
        temp_extract_dir = Path(output_dir) / 'temp_extracted'
        os.makedirs(temp_extract_dir, exist_ok=True)

        main_extracted_dir = extract_zip(subset_path, temp_extract_dir)
        trips_file_path = main_extracted_dir / 'trips.txt'
        stop_times_file_path = main_extracted_dir / 'stop_times.txt'

        filtered_trips_df = filter_trips(trips_file_path, direction_flag)
        trip_ids = filtered_trips_df['trip_id'].tolist()
        filtered_stop_times_df = filter_stop_times(stop_times_file_path, trip_ids)

        # Save filtered files back to the extracted directory
        filtered_trips_df.to_csv(trips_file_path, index=False)
        filtered_stop_times_df.to_csv(stop_times_file_path, index=False)

        # Create temporary zip file and read its contents
        new_zip_name = Path(output_dir) / output_file
        create_new_zip(main_extracted_dir, new_zip_name)
        
        print(f"Successfully created output file: {new_zip_name}")
        return new_zip_name
        
    except Exception as e:
        print(f"Error processing GTFS data: {str(e)}", file=sys.stderr)
        raise

def main():
    parser = argparse.ArgumentParser(description='Process GTFS data with filtering and visualization')
    
    # Required arguments
    parser.add_argument('input_gtfs', help='Path to input GTFS file')
    parser.add_argument('target_stops', nargs='+', help='One or more target stop IDs to create subset around')
    
    # Optional arguments
    parser.add_argument('--output-dir', default='examples',
                      help='Output directory (default: examples)')
    parser.add_argument('--min-trips', type=int, default=5,
                      help='Minimum daily trips for route inclusion (default: 5)')
    parser.add_argument('--important-stops-only', action='store_true',
                      help='Only include junction and terminal stops (default: False)')
    parser.add_argument('--hide-routes', action='store_true',
                      help='Disable route visualization (default: False)')
    parser.add_argument('--direction', type=int, default=0,
                      help='Direction flag (0 for down, 1 for up) (default: 0)')
    parser.add_argument('--output', default='subset_filtered.zip',
                      help='Output GTFS file (default: subset_filtered.zip)')
    parser.add_argument('--skip-direction-filter', action='store_true',
                      help='Skip direction filtering and keep all trips (default: False)')
    parser.add_argument('--viz-file', default='network_stops.html',
                      help='Visualization file name (default: network_stops.html)')

    args = parser.parse_args()
    
    process_gtfs_complete(
        args.input_gtfs,
        args.target_stops,
        args.output_dir,
        args.min_trips,
        args.important_stops_only,
        not args.hide_routes,
        args.skip_direction_filter,
        args.direction,
        args.output,
        args.viz_file
    )

if __name__ == "__main__":
    main() 