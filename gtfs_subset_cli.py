#!/usr/bin/env python3
import argparse
from gtfs_analysis import GTFSAnalyzer
from gtfs_map_viewer import GTFSMapCreator
from pathlib import Path
import sys

def create_subset(input_gtfs: str, *, 
                 output: str = None,
                 stops: str = None,
                 routes: str = None,
                 min_trips: int = None,
                 map: bool = False,
                 map_output: str = None,
                 stops_only: bool = False,
                 color_by: str = 'trips',
                 cmap: str = 'magma',
                 route_cmap: str = 'tab20c',
                 **kwargs) -> Path:
    """
    Create a GTFS subset with optional map visualization.
    Uses keyword-only arguments for clarity and safety.
    Route colors are always applied using the specified colormap.

    
    Additional Parameters:
    ---------------------
    apply_colors : bool
        If True, generates and prints route colors using the specified colormap
    Example usage:
        # Basic subsetting
        python gtfs_subset_cli.py input.zip -o output.zip
        
        # Filter by stops
        python gtfs_subset_cli.py input.zip -s "STOP1,STOP2,STOP3"
        
        # Filter by routes (with wildcards)
        python gtfs_subset_cli.py input.zip -r "138*,KBS*"
        
        # Filter by minimum trips
        python gtfs_subset_cli.py input.zip -m 10
        
        # Combine filters and create map
        python gtfs_subset_cli.py input.zip -s "STOP1,STOP2" -r "138*" -m 10 --map
        
        # Create map with custom coloring
        python gtfs_subset_cli.py input.zip --map --color-by routes --cmap viridis --route-cmap plasma
        
        # Show only stops on map
        python gtfs_subset_cli.py input.zip --map --stops-only
    """
    # Parse filters
    stop_ids = [s.strip() for s in stops.split(',')] if stops else None
    route_patterns = [r.strip() for r in routes.split(',')] if routes else None
    
    # Generate output name if not provided
    if not output:
        filters = []
        if stop_ids:
            filters.append(f"stops_{'-'.join(stop_ids)}")
        if route_patterns:
            filters.append(f"routes_{'-'.join(route_patterns)}")
        if min_trips:
            filters.append(f"min{min_trips}")
        output = str(Path(input_gtfs).resolve().with_name(
            f"{Path(input_gtfs).stem}_{'_'.join(filters or ['full'])}.zip"
        ))
    
    # Create analyzer instance
    analyzer = GTFSAnalyzer(input_gtfs)
    
    # Create subset (colors will be applied during subsetting)
    subset = analyzer.create_subset(
        output_path=output,
        stop_ids=stop_ids,
        route_patterns=route_patterns,
        min_trips=min_trips
    )
    
    # Print statistics to stderr
    print(f"\nSubset Statistics:", file=sys.stderr)
    print(f"Original routes: {len(analyzer.feed.routes)}", file=sys.stderr)
    print(f"Subset routes: {len(subset.feed.routes)}", file=sys.stderr)
    print(f"Original trips: {len(analyzer.feed.trips)}", file=sys.stderr)
    print(f"Subset trips: {len(subset.feed.trips)}", file=sys.stderr)
    print(f"Original stops: {len(analyzer.feed.stops)}", file=sys.stderr)
    print(f"Subset stops: {len(subset.feed.stops)}", file=sys.stderr)
    
    # Create map if requested
    if map:
        map_path = map_output or str(Path(output).with_suffix('.html'))
        map_creator = GTFSMapCreator(output)
        map_creator.load_gtfs_data()
        map_creator.create_map(
            output_path=map_path,
            stops_only=stops_only,
            color_by=color_by,
            cmap=cmap,
            route_cmap=route_cmap,
            **kwargs
        )
        print(f"Map created at: {map_path}", file=sys.stderr)
    
    # Print the output path as the last line
    print(output, file=sys.stderr)
    return Path(output)

def main():
    parser = argparse.ArgumentParser(
        description='Create GTFS subsets based on various filters'
    )
    parser.add_argument('input_gtfs', help='Path to input GTFS zip file')
    parser.add_argument('-o', '--output', help='Output GTFS path')
    parser.add_argument('-s', '--stops', help='Comma-separated stop IDs')
    parser.add_argument('-r', '--routes', help='Comma-separated route patterns (wildcards supported)')
    parser.add_argument('-m', '--min-trips', type=int, help='Minimum trips per route')
    parser.add_argument('--map', action='store_true', help='Create HTML map')
    parser.add_argument('--map-output', help='Map output path')
    parser.add_argument('--stops-only', action='store_true', help='Show only stops on map')
    parser.add_argument('--color-by', choices=['trips', 'routes'], default='trips',
                      help='Metric to use for coloring stops')
    parser.add_argument('--cmap', default='magma',
                      help='Matplotlib colormap name for stops')
    parser.add_argument('--route-cmap', default='tab20c',
                      help='Matplotlib colormap name for routes (default: tab20c)')

    args = parser.parse_args()
    create_subset(**vars(args))

if __name__ == '__main__':
    main()