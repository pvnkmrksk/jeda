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

def process_gtfs_complete(input_path: str, target_stop: str, output_dir: str="examples", 
                         min_trips: int=5, important_stops: bool=True, show_routes: bool=True,
                         direction_flag: int=0, output_file='subset_filtered.zip'):
    """Combined processing function that handles the entire workflow"""
    
    os.makedirs(output_dir, exist_ok=True)
    subset_path = os.path.join(output_dir, "subset.zip")
    
    # Step 1: Create GTFS subset
    result = create_gtfs_subset(
        feed_path=input_path,
        target_stop_id=target_stop,
        output_path=subset_path,
        min_daily_trips=min_trips,
        only_important_stops=important_stops
    )
    
    # Step 2: Create visualization if requested
    if show_routes:
        viz_path = os.path.join(output_dir, f"network_stops_{target_stop}.html")
        map_viz = visualize_stops(
            result['full']['feed'],
            result['stops'],
            show_routes=True
        )
        map_viz.save(viz_path)
    
    # Step 3: Filter by direction
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
    new_zip_name = Path(output_file)
    create_new_zip(main_extracted_dir, new_zip_name)
    
    # Cleanup
    shutil.rmtree(temp_extract_dir)
    os.remove(subset_path)
    
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
    parser.add_argument('--output', default='subset_filtered.zip',
                      help='Output GTFS file (default: subset_filtered.zip)')

    args = parser.parse_args()
    
    process_gtfs_complete(
        args.input_gtfs,
        args.target_stop,
        args.output_dir,
        args.min_trips,
        args.important_stops_only,
        not args.hide_routes,
        args.direction
    )

if __name__ == "__main__":
    main() 