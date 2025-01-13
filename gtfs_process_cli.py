#!/usr/bin/env python3

import argparse
import os
from pathlib import Path
import partridge as ptg
import folium


def create_gtfs_subset(feed_path: str, target_stop_ids: list, output_path: str, min_daily_trips: int = 5):
    """
    Create a subset of the GTFS feed containing specific stops and frequent routes.
    """
    # Load the feed with a minimal view
    feed = ptg.load_feed(feed_path, view={'stop_times.txt': None, 'trips.txt': None})

    # Filter stop_times for target stops
    stop_times = feed.stop_times
    stop_mask = stop_times['stop_id'].isin(target_stop_ids)
    stop_times_at_targets = stop_times[stop_mask]

    # Get trips serving the target stops
    trips_at_targets = stop_times_at_targets['trip_id'].unique()
    
    # Get route frequencies
    trip_to_route = feed.trips.set_index('trip_id')['route_id']
    route_counts = trip_to_route.loc[trips_at_targets].value_counts()
    frequent_routes = route_counts[route_counts >= min_daily_trips].index

    # Filter trips for frequent routes
    frequent_trip_ids = feed.trips[feed.trips['route_id'].isin(frequent_routes)]['trip_id']

    # Create a subset view
    view = {
        'trips.txt': {'trip_id': set(frequent_trip_ids)},
        'stop_times.txt': {'trip_id': set(frequent_trip_ids)},
        'stops.txt': {'stop_id': set(target_stop_ids)},
    }

    # Extract the subset
    ptg.extract_feed(feed_path, output_path, view)
    print(f"Subset saved to: {output_path}")
    return output_path


def visualize_stops(feed_path: str, target_stop_ids: list, output_path: str, zoom_start=12):
    """
    Visualize stops on a map and save as an HTML file.
    """
    feed = ptg.load_feed(feed_path, view={'stops.txt': None})
    stops = feed.stops
    m = folium.Map(
        location=[stops['stop_lat'].mean(), stops['stop_lon'].mean()],
        zoom_start=zoom_start
    )

    for _, stop in stops.iterrows():
        color = 'red' if stop['stop_id'] in target_stop_ids else 'blue'
        folium.CircleMarker(
            location=[stop['stop_lat'], stop['stop_lon']],
            radius=5,
            color=color,
            fill=True,
            fill_opacity=0.7,
            popup=f"{stop['stop_name']} ({stop['stop_id']})"
        ).add_to(m)

    m.save(output_path)
    print(f"Map visualization saved to: {output_path}")


def warn_deprecated_flags(**flags):
    """
    Issue warnings for deprecated or unused flags.
    """
    for flag, value in flags.items():
        if value is not None:
            print(f"Warning: The flag '--{flag.replace('_', '-')}' is deprecated and has no effect.", flush=True)


def main():
    parser = argparse.ArgumentParser(description='GTFS Subset and Visualization Tool')
    parser.add_argument('input_gtfs', help='Path to input GTFS zip file')
    parser.add_argument('target_stops', nargs='+', help='Target stop IDs for filtering')
    parser.add_argument('--output-dir', default='output', help='Output directory (default: output)')
    parser.add_argument('--min-trips', type=int, default=5, help='Minimum daily trips for route inclusion')
    parser.add_argument('--viz-file', default='stops_map.html', help='Output HTML file for visualization')

    # Deprecated/unused flags
    parser.add_argument('--important-stops-only', action='store_true', help='(Deprecated) Only include junction and terminal stops')
    parser.add_argument('--hide-routes', action='store_true', help='(Deprecated) Disable route visualization')
    parser.add_argument('--direction', type=int, default=None, help='(Deprecated) Direction flag (0 for down, 1 for up)')
    parser.add_argument('--skip-direction-filter', action='store_true', help='(Deprecated) Skip direction filtering')
    parser.add_argument('--advanced-processing', action='store_true', help='(Deprecated) Enable advanced stop processing features')

    args = parser.parse_args()

    # Warn about deprecated flags
    warn_deprecated_flags(
        important_stops_only=args.important_stops_only,
        hide_routes=args.hide_routes,
        direction=args.direction,
        skip_direction_filter=args.skip_direction_filter,
        advanced_processing=args.advanced_processing
    )

    # Prepare paths
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    subset_path = output_dir / "subset_gtfs.zip"
    viz_path = output_dir / args.viz_file

    # Process GTFS
    create_gtfs_subset(args.input_gtfs, args.target_stops, str(subset_path), args.min_trips)
    visualize_stops(str(subset_path), args.target_stops, str(viz_path))


if __name__ == "__main__":
    main()