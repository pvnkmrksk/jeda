#!/usr/bin/env python3
import argparse
from gtfs_analysis import GTFSAnalyzer
from gtfs_map_viewer import GTFSMapCreator
from pathlib import Path

def parse_list_arg(arg: str) -> list:
    """Parse comma-separated string into list"""
    return [item.strip() for item in arg.split(',')] if arg else None

def generate_output_name(input_path: str, stops: list = None, 
                        routes: list = None, min_trips: int = None) -> str:
    """Generate a descriptive output filename based on applied filters"""
    base = Path(input_path).stem
    filters = []
    
    if stops:
        filters.append(f"stops_{'-'.join(stops)}")
    if routes:
        filters.append(f"routes_{'-'.join(routes)}")
    if min_trips:
        filters.append(f"min{min_trips}")
        
    return f"{base}_{'_'.join(filters or ['full'])}.zip"

def create_map(gtfs_path: str, map_output: str = None, stops_only: bool = False):
    """Create an interactive map from the GTFS data"""
    map_output = map_output or str(Path(gtfs_path).with_suffix('.html'))
    map_creator = GTFSMapCreator(gtfs_path)
    map_creator.load_gtfs_data()
    map_creator.create_map(map_output, stops_only=stops_only)
    print(f"Map created at: {map_output}")

def main():
    parser = argparse.ArgumentParser(
        description='Create GTFS subsets based on various filters'
    )
    parser.add_argument(
        'input_gtfs',
        help='Path to input GTFS zip file'
    )
    parser.add_argument(
        '-o', '--output',
        help='Path where output GTFS zip will be saved (optional)'
    )
    parser.add_argument(
        '-s', '--stops',
        help='Comma-separated list of stop IDs to filter by'
    )
    parser.add_argument(
        '-r', '--routes',
        help='Comma-separated list of route patterns to filter by (supports wildcards)'
    )
    parser.add_argument(
        '-m', '--min-trips',
        type=int,
        help='Minimum number of trips a route must have'
    )
    parser.add_argument(
        '--map',
        action='store_true',
        help='Create an interactive HTML map of the subset'
    )
    parser.add_argument(
        '--map-output',
        help='Path for the output HTML map (default: {gtfs_name}.html)'
    )
    parser.add_argument(
        '--stops-only',
        action='store_true',
        help='Show only stops on the map, no routes'
    )

    args = parser.parse_args()
    
    # Parse arguments and create subset
    stops = parse_list_arg(args.stops)
    routes = parse_list_arg(args.routes)
    output_path = args.output or generate_output_name(
        args.input_gtfs, stops, routes, args.min_trips
    )

    analyzer = GTFSAnalyzer(args.input_gtfs)
    subset = analyzer.create_subset(
        output_path=output_path,
        stop_ids=stops,
        route_patterns=routes,
        min_trips=args.min_trips
    )
    
    # Print statistics
    print(f"\nOutput GTFS: {output_path}")
    print(f"\nSubset Statistics:")
    print(f"Original routes: {len(analyzer.feed.routes)}")
    print(f"Subset routes: {len(subset.feed.routes)}")
    print(f"Original trips: {len(analyzer.feed.trips)}")
    print(f"Subset trips: {len(subset.feed.trips)}")
    print(f"Original stops: {len(analyzer.feed.stops)}")
    print(f"Subset stops: {len(subset.feed.stops)}")
    
    if args.map:
        create_map(output_path, args.map_output, args.stops_only)

if __name__ == '__main__':
    main()