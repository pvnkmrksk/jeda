#!/usr/bin/env python3

"""
GTFS Subset CLI Tool
===================

Part of the Magga (ಮಗ್ಗ/मग्ग) project - A transit map generation toolkit.

"Magga" carries dual meaning - a loom (ಮಗ್ಗ) in Kannada that weaves intricate
patterns, and "path" (मग्ग) in Pali Buddhism, referring to the noble path to
enlightenment. Much like how a loom weaves threads into beautiful patterns,
public transit weaves paths through our cities. And just as the Noble Eightfold
Path guides beings toward enlightenment, accessible public transit guides
communities toward sustainability and equity - reducing emissions, connecting
people to opportunities, and weaving the fabric of more livable cities.

A command-line tool for creating filtered subsets of GTFS data based on various
criteria such as specific stops, routes, or minimum trip counts.

For more information, visit: https://github.com/pvnkmrksk/magga

MIT License

Copyright (c) 2024 Pavan Kumar (@pvnkmrksk)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

This work builds upon the LOOM project (https://github.com/ad-freiburg/loom)
and is distributed under compatible terms.

Author: ಪವನ ಕುಮಾರ ​| Pavan Kumar, PhD (@pvnkmrksk)
"""

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
    Create a filtered GTFS subset with optional map visualization.

    This function provides a high-level interface for filtering GTFS data based on
    various criteria and optionally generating a visualization of the result.

    Args:
        input_gtfs (str): Path to input GTFS zip file
        output (str, optional): Output path for the filtered GTFS
        stops (str, optional): Comma-separated stop IDs to include
        routes (str, optional): Route patterns to match (supports wildcards)
        min_trips (int, optional): Minimum trips per route
        map (bool, optional): Generate HTML map visualization
        map_output (str, optional): Custom path for map output
        stops_only (bool, optional): Show only stops on map
        color_by (str, optional): Metric for coloring ('trips'/'routes')
        cmap (str, optional): Matplotlib colormap for stops
        route_cmap (str, optional): Matplotlib colormap for routes
        **kwargs: Additional parameters passed to map creation

    Returns:
        Path: Path to the generated GTFS subset

    Example:
        >>> create_subset('input.zip',
        ...              stops='STOP1,STOP2',
        ...              routes='138*',
        ...              min_trips=10,
        ...              map=True)
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
        description='''
Magga (ಮಗ್ಗ/मग्ग) GTFS Subset Generator
====================================

Drawing inspiration from both the Kannada word for loom (ಮಗ್ಗ) and the Pali word
for path (मग्ग), this tool helps select and filter GTFS data to create focused
transit maps. Just as a loom carefully selects threads for a pattern, and the
Noble Path guides toward enlightenment, this tool helps illuminate the transit
paths that connect communities to opportunities.

Create filtered subsets of GTFS data based on various criteria such as stops,
routes, or minimum trip counts. Optionally generate interactive visualizations
of the resulting network.
''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Input/Output
    parser.add_argument('input_gtfs', 
                       help='Path to input GTFS zip file')
    parser.add_argument('-o', '--output',
                       help='Output path for filtered GTFS (default: auto-generated)')
    
    # Filtering Options
    filter_group = parser.add_argument_group('filtering options')
    filter_group.add_argument('-s', '--stops',
                            help='Comma-separated stop IDs to include')
    filter_group.add_argument('-r', '--routes',
                            help='Route patterns to match (supports wildcards)')
    filter_group.add_argument('-m', '--min-trips',
                            type=int,
                            help='Minimum trips per route')
    
    # Visualization Options
    viz_group = parser.add_argument_group('visualization options')
    viz_group.add_argument('--map',
                          action='store_true',
                          help='Generate interactive HTML map')
    viz_group.add_argument('--map-output',
                          help='Custom path for map output (default: input_name.html)')
    viz_group.add_argument('--stops-only',
                          action='store_true',
                          help='Show only stops on map (no routes)')
    viz_group.add_argument('--color-by',
                          choices=['trips', 'routes'],
                          default='trips',
                          help='Metric for coloring stops (default: trips)')
    
    # Style Options
    style_group = parser.add_argument_group('style options')
    style_group.add_argument('--cmap',
                            default='magma',
                            help='Matplotlib colormap for stops (default: magma)')
    style_group.add_argument('--route-cmap',
                            default='tab20c',
                            help='Matplotlib colormap for routes (default: tab20c)')

    parser.epilog = '''
examples:
  # Basic subsetting
  %(prog)s input.zip -o output.zip

  # Filter by stops
  %(prog)s input.zip -s "STOP1,STOP2,STOP3"

  # Filter by routes with wildcards
  %(prog)s input.zip -r "138*,KBS*"

  # Filter by minimum trips
  %(prog)s input.zip -m 10

  # Generate map with custom coloring
  %(prog)s input.zip --map --color-by routes --cmap viridis

  # Complex filtering with visualization
  %(prog)s input.zip -s "STOP1,STOP2" -r "138*" -m 10 --map

notes:
  - Route patterns support wildcards (e.g., "138*" matches "138A", "138B")
  - Generated subsets preserve the organic flow of transit routes
  - Colormaps can be chosen from matplotlib's collection
  - Output includes both data and optional visualization

For more information and documentation:
  https://github.com/pvnkmrksk/magga
'''

    args = parser.parse_args()
    create_subset(**vars(args))

if __name__ == '__main__':
    main()