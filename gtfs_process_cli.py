#!/usr/bin/env python3

import argparse
import os
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

def process_gtfs_complete(input_path: str, target_stop: str, output_dir: str="examples", 
                         min_trips: int=5, important_stops: bool=True, show_routes: bool=True,
                         direction_flag: int=0):
    """Combined processing function that handles the entire workflow"""
    
    os.makedirs(output_dir, exist_ok=True)
    subset_path = os.path.join(output_dir, "subset.zip")
    viz_path = os.path.join(output_dir, f"network_stops_{target_stop}.html")
    
    # Step 1: Create GTFS subset
    print(f"Creating GTFS subset for stop {target_stop}...")
    result = create_gtfs_subset(
        feed_path=input_path,
        target_stop_id=target_stop,
        output_path=subset_path,
        min_daily_trips=min_trips,
        only_important_stops=important_stops
    )
    
    # Step 2: Create visualization if requested
    if show_routes:
        print("Creating visualization...")
        map_viz = visualize_stops(
            result['full']['feed'],
            result['stops'],
            show_routes=True
        )
        map_viz.save(viz_path)
        print(f"Visualization saved to {viz_path}")
    
    # Step 3: Filter by direction
    zip_dir = Path(subset_path).parent
    temp_extract_dir = zip_dir / 'temp_extracted'
    os.makedirs(temp_extract_dir, exist_ok=True)

    main_extracted_dir = extract_zip(subset_path, temp_extract_dir)
    trips_file_path = main_extracted_dir / 'trips.txt'
    stop_times_file_path = main_extracted_dir / 'stop_times.txt'

    filtered_trips_df = filter_trips(trips_file_path, direction_flag)
    trip_ids = filtered_trips_df['trip_id'].tolist()
    filtered_stop_times_df = filter_stop_times(stop_times_file_path, trip_ids)

    # Save filtered files
    new_dir = zip_dir / 'modified_files'
    os.makedirs(new_dir, exist_ok=True)

    shutil.copytree(main_extracted_dir, new_dir, dirs_exist_ok=True)
    filtered_trips_df.to_csv(new_dir / 'trips.txt', index=False)
    filtered_stop_times_df.to_csv(new_dir / 'stop_times.txt', index=False)

    # Create final zip file
    direction_suffix = '_up' if direction_flag == 1 else '_down'
    new_zip_name = zip_dir / f"subset{direction_suffix}.zip"
    create_new_zip(new_dir, new_zip_name)

    print(f"Final processed zip file created: {new_zip_name}")
    shutil.rmtree(temp_extract_dir)  # Clean up
    
    return new_zip_name

def main():
    parser = argparse.ArgumentParser(description='Process GTFS data with filtering and visualization')
    
    # Required arguments
    parser.add_argument('input_gtfs', help='Path to input GTFS file')
    parser.add_argument('target_stop', help='Target stop ID to create subset around')
    
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

    args = parser.parse_args()
    
    final_zip = process_gtfs_complete(
        args.input_gtfs,
        args.target_stop,
        args.output_dir,
        args.min_trips,
        args.important_stops_only,
        not args.hide_routes,
        args.direction
    )
    
    print(f"Processing complete. Final output: {final_zip}")

if __name__ == "__main__":
    main() 