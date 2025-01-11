# #!/usr/bin/env python3

# import argparse
# import os
# import partridge as ptg
# import folium
# import random
# from pathlib import Path
# import subprocess
# from typing import Union, List




# def process_gtfs(input_path, target_stop, output_dir="examples", 
#                 min_trips=5, important_stops=True, show_routes=True):
#     """Main processing function that handles the entire workflow"""
    
#     os.makedirs(output_dir, exist_ok=True)
    
#     subset_path = os.path.join(output_dir, "subset.zip")
#     viz_path = os.path.join(output_dir, f"network_stops_{target_stop}.html")
    
#     print(f"Creating GTFS subset for stop {target_stop}...")
#     result = create_gtfs_subset(
#         feed_path=input_path,
#         target_stop_id=target_stop,
#         output_path=subset_path,
#         min_daily_trips=min_trips,
#         only_important_stops=important_stops
#     )
    
#     full_feed = result['full']['feed']
#     stop_types = result['stops']
    
#     print(f"Created subset with {len(full_feed.stops)} total stops")
#     print(f"Found {len(stop_types['junction'])} junction stops")
#     print(f"Found {len(stop_types['terminal'])} terminal stops")
    
#     print("Creating visualization...")
#     map_viz = visualize_stops(
#         full_feed, 
#         stop_types,
#         show_routes=show_routes
#     )
#     map_viz.save(viz_path)
#     print(f"Visualization saved to {viz_path}")
    
#     return True

# def main():
#     parser = argparse.ArgumentParser(description='Create GTFS subset and generate visualizations')
    
#     # Required arguments
#     parser.add_argument('input_gtfs', help='Path to input GTFS file')
#     parser.add_argument('target_stop', help='Target stop ID to create subset around')
    
#     # Optional arguments
#     parser.add_argument(
#         '--output-dir', 
#         default='examples',
#         help='Output directory (default: examples)'
#     )
#     parser.add_argument(
#         '--min-trips', 
#         type=int, 
#         default=5,
#         help='Minimum daily trips for route inclusion (default: 5)'
#     )
#     parser.add_argument(
#         '--important-stops-only', 
#         action='store_true',
#         help='Only include junction and terminal stops (default: False)'
#     )
#     parser.add_argument(
#         '--hide-routes', 
#         action='store_true',
#         help='Disable route visualization (default: False)'
#     )

#     args = parser.parse_args()
    
#     success = process_gtfs(
#         args.input_gtfs,
#         args.target_stop,
#         args.output_dir,
#         args.min_trips,
#         args.important_stops_only,
#         not args.hide_routes
#     )
    
#     exit(0 if success else 1)

# if __name__ == "__main__":
#     main() 