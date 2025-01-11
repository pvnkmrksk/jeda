#!/usr/bin/env python3

import argparse
import os
import sys
import shutil
from pathlib import Path

# Import functions from existing files
from zip_filter_cli import (
    extract_zip,
    filter_trips,
    filter_stop_times,
    create_new_zip
)

from gtfs_subset_cli import (
    find_true_junctions,
    create_gtfs_subset,
    visualize_stops
)

def process_gtfs_complete(input_path: str, target_stops: list[str], output_dir: str="examples", 
                         min_trips: int=5, important_stops: bool=True, show_routes: bool=True,
                         skip_direction_filter: bool=True , direction_flag: int=1, 
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
        args.target_stops,  # Now passing a list
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