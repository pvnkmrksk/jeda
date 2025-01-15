# #!/usr/bin/env python3

# import argparse
# import os
# import re
# from pathlib import Path
# import partridge as ptg
# import folium


# def create_gtfs_subset(feed_path: str, target_stop_ids: list, output_path: str, min_daily_trips: int = 5, target_route_patterns: list = None):
#     """
#     Create a subset of the GTFS feed containing specific stops and/or routes.
#     Returns the actual path of the created file.
#     """
#     # Load the feed with a complete view first
#     feed = ptg.load_feed(feed_path)
    
#     filtered_trip_ids = set()
    
#     # Filter by routes if specified
#     if target_route_patterns:
#         routes = feed.routes
#         matching_routes = set()
#         for pattern in target_route_patterns:
#             # Convert pattern to string and handle exact matches
#             pattern_str = str(pattern)
#             if '*' not in pattern_str:
#                 # Exact match
#                 matching_routes.update(routes[routes['route_id'] == pattern_str]['route_id'])
#             else:
#                 # Wildcard match
#                 regex = re.compile('^' + re.escape(pattern_str).replace('\\*', '.*') + '$')
#                 matching_routes.update(routes[routes['route_id'].str.match(regex)]['route_id'])
        
#         if matching_routes:
#             route_trips = feed.trips[feed.trips['route_id'].isin(matching_routes)]['trip_id']
#             filtered_trip_ids.update(route_trips)
#         else:
#             print(f"Warning: No routes found matching patterns: {target_route_patterns}")
    
#     # Filter by stops if specified and not empty
#     if target_stop_ids and any(target_stop_ids):
#         stop_times = feed.stop_times
#         stop_mask = stop_times['stop_id'].isin(target_stop_ids)
#         stop_trips = set(stop_times[stop_mask]['trip_id'].unique())
        
#         if filtered_trip_ids:
#             # If we already have route-filtered trips, take intersection
#             filtered_trip_ids.intersection_update(stop_trips)
#         else:
#             filtered_trip_ids = stop_trips
    
#     # If no filters were applied or no matches found, use all trips
#     if not filtered_trip_ids:
#         if (target_stop_ids and any(target_stop_ids)) or target_route_patterns:
#             print("Warning: No trips found matching the specified filters")
#         filtered_trip_ids = set(feed.trips['trip_id'])
    
#     # Filter by minimum trips per route
#     trips_df = feed.trips[feed.trips['trip_id'].isin(filtered_trip_ids)]
#     route_counts = trips_df['route_id'].value_counts()
#     frequent_routes = route_counts[route_counts >= min_daily_trips].index
#     final_trip_ids = set(trips_df[trips_df['route_id'].isin(frequent_routes)]['trip_id'])
    
#     if not final_trip_ids:
#         print(f"Warning: No routes found with at least {min_daily_trips} trips")
#         return None
    
#     # Get all stops served by these trips
#     all_used_stops = set(feed.stop_times[feed.stop_times['trip_id'].isin(final_trip_ids)]['stop_id'])
    
#     # Create the view for extraction
#     view = {
#         'trips.txt': {'trip_id': final_trip_ids},
#         'stop_times.txt': {'trip_id': final_trip_ids},
#         'stops.txt': {'stop_id': all_used_stops},
#         'routes.txt': {'route_id': frequent_routes}
#     }
    
#     # Extract the subset
#     ptg.extract_feed(feed_path, output_path, view)
    
#     # Print some statistics
#     print(f"\nSubset statistics:")
#     print(f"Selected {len(final_trip_ids)} trips")
#     print(f"Selected {len(frequent_routes)} routes")
#     print(f"Selected {len(all_used_stops)} stops")
#     if target_route_patterns:
#         print(f"Route patterns matched: {matching_routes}")
    
#     # Return the actual output path that was created
#     return output_path


# def visualize_stops(feed_path: str, target_stop_ids: list, output_path: str, zoom_start=12):
#     """
#     Visualize stops on a map and save as an HTML file.
#     """
#     feed = ptg.load_feed(feed_path, view={'stops.txt': None})
#     stops = feed.stops
#     m = folium.Map(
#         location=[stops['stop_lat'].mean(), stops['stop_lon'].mean()],
#         zoom_start=zoom_start
#     )

#     for _, stop in stops.iterrows():
#         color = 'red' if target_stop_ids and stop['stop_id'] in target_stop_ids else 'blue'
#         folium.CircleMarker(
#             location=[stop['stop_lat'], stop['stop_lon']],
#             radius=5,
#             color=color,
#             fill=True,
#             fill_opacity=0.7,
#             popup=f"{stop['stop_name']} ({stop['stop_id']})"
#         ).add_to(m)

#     m.save(output_path)
#     print(f"Map visualization saved to: {output_path}")


# def warn_deprecated_flags(**flags):
#     """
#     Issue warnings for deprecated or unused flags.
#     """
#     for flag, value in flags.items():
#         if value is not None:
#             print(f"Warning: The flag '--{flag.replace('_', '-')}' is deprecated and has no effect.", flush=True)


# def parse_route_patterns(patterns: list):
#     """
#     Parse route patterns into regex patterns for filtering.
#     Supports simple wildcard (*) matching and regex.
#     """
#     regex_patterns = []
#     for pattern in patterns:
#         if '*' in pattern:
#             # Convert wildcard to regex
#             regex_patterns.append(re.escape(pattern).replace(r'\*', '.*'))
#         else:
#             # Treat as exact match or regex
#             regex_patterns.append(pattern)
#     return regex_patterns


# def main():
#     parser = argparse.ArgumentParser(description='GTFS Subset and Visualization Tool')
#     parser.add_argument('--input-gtfs', required=True, help='Path to input GTFS zip file')
#     parser.add_argument('--target-stops', nargs='*', default=None, help='Target stop IDs for filtering')
#     parser.add_argument('--target-routes', nargs='+', help='Route patterns for filtering (e.g., 314*)')
#     parser.add_argument('--output-dir', default='output', help='Output directory (default: output)')
#     parser.add_argument('--min-trips', type=int, default=5, help='Minimum daily trips for route inclusion')
#     parser.add_argument('--viz-file', default='stops_map.html', help='Output HTML file for visualization')

#     # Deprecated/unused flags
#     parser.add_argument('--important-stops-only', action='store_true', help='(Deprecated) Only include junction and terminal stops')
#     parser.add_argument('--hide-routes', action='store_true', help='(Deprecated) Disable route visualization')
#     parser.add_argument('--direction', type=int, default=None, help='(Deprecated) Direction flag (0 for down, 1 for up)')
#     parser.add_argument('--skip-direction-filter', action='store_true', help='(Deprecated) Skip direction filtering')
#     parser.add_argument('--advanced-processing', action='store_true', help='(Deprecated) Enable advanced stop processing features')

#     args = parser.parse_args()

#     # Warn about deprecated flags
#     warn_deprecated_flags(
#         important_stops_only=args.important_stops_only,
#         hide_routes=args.hide_routes,
#         direction=args.direction,
#         skip_direction_filter=args.skip_direction_filter,
#         advanced_processing=args.advanced_processing
#     )

#     # Parse route patterns
#     target_route_patterns = parse_route_patterns(args.target_routes) if args.target_routes else None

#     # Clean up target stops - filter out empty strings and None values
#     target_stops = [stop for stop in (args.target_stops or []) if stop and stop.strip()]
    
#     # Prepare paths
#     output_dir = Path(args.output_dir)
#     output_dir.mkdir(parents=True, exist_ok=True)
    
#     # Generate base filename from parameters - use cleaned target_stops
#     stops_str = '_'.join(target_stops) if target_stops else ''
#     routes_str = '_'.join(args.target_routes) if args.target_routes else ''
#     base_filename = f"BMTC_transit_{stops_str}_{routes_str}_m{args.min_trips}"
    
#     # Use consistent filenames
#     subset_path = output_dir / f"{base_filename}.zip"
#     viz_path = output_dir / args.viz_file

#     # Process GTFS with cleaned target stops
#     output_file = create_gtfs_subset(
#         feed_path=args.input_gtfs,
#         target_stop_ids=target_stops,
#         target_route_patterns=target_route_patterns,
#         output_path=str(subset_path),
#         min_daily_trips=args.min_trips
#     )
    
#     # Print the actual output path for the shell script to capture
#     print(f"OUTPUT_FILE={output_file}", flush=True)

#     # visualize_stops(
#     #     feed_path=str(subset_path),
#     #     target_stop_ids=args.target_stops,
#     #     output_path=str(viz_path)
#     # )


# if __name__ == "__main__":
#     main()