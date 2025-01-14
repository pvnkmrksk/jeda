#!/bin/bash

# Show help if no arguments or help flag
if [ $# -eq 0 ] || [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    echo "Usage: $0 <zip_pattern>"
    echo "Example: $0 'stop_analysis/subsets/*.zip'"
    echo "Process GTFS zip files matching the given pattern through the map viewer"
    exit 0
fi

# Get total count of files to process
total=$(find $1 -type f | wc -l)
echo "Processing $total GTFS files..."

# Process files with simplified progress output
find $1 -type f | \
parallel --joblog process_log.txt \
    'echo "Processing {/.} ($PARALLEL_SEQ of '$total')" && \
     python gtfs_map_viewer.py {} && \
     echo "✓ Completed {/.}"' 