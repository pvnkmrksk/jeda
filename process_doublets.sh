#!/bin/bash

if [ $# -eq 0 ] || [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    echo "Usage: $0 <gtfs_file>"
    echo "Process GTFS file for each doublet stop pair"
    exit 0
fi

GTFS_FILE=$1
OUTPUT_DIR="doublet_output"
START_ROW=30

mkdir -p "$OUTPUT_DIR"

# Skip to row 30 and process one at a time
row_num=1
while IFS=, read -r _ name id1 id2 _; do
    if [ $row_num -lt $START_ROW ]; then
        row_num=$((row_num + 1))
        continue
    fi
    
    # Clean the name and IDs
    clean_name=$(echo "$name" | tr -d '"' | tr ' /' '_' | tr -d '()')
    id1=$(echo "$id1" | tr -d ' ')
    id2=$(echo "$id2" | tr -d ' ')
    
    echo "Processing $clean_name (stops: $id1,$id2)..."
    
    # Create directory and run transit map
    pair_dir="$OUTPUT_DIR/$clean_name"
    mkdir -p "$pair_dir"
    ./process_transit_map.sh "$GTFS_FILE" --stops "$id1,$id2" --output-dir "$pair_dir" --min-trips 15
    
    row_num=$((row_num + 1))
done < <(tail -n +2 Doublet_stops.csv) 