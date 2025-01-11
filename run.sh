#!/bin/bash

# Default values for variables
GTFS_FILE="bmtc-2.zip"
CSV_FILE="stop_trip_counts.csv"
OUTPUT_DIR="output"
MIN_TRIPS=5
OUTPUT_FILE_PREFIX="subset_filtered"
OCTI_ENABLED=false
COLORMAP="tab20c"
IMPORTANT_STOPS=false
HIDE_ROUTES=false
DIRECTION=0
SKIP_DIRECTION=false
# Define the list of stop IDs you want to process
STOP_IDS=("5wx" "32p")
# Function to display usage
usage() {
    echo "Usage: $0 [-g gtfs_file] [-c csv_file] [-o output_dir] [-m min_trips] [-p output_file_prefix] [-x] [-l colormap] [-i] [-r] [-d direction] [-s]"
    echo "  -g  GTFS file (default: $GTFS_FILE)"
    echo "  -t  Stop IDs (space-separated list, default: ${STOP_IDS[*]})"
    echo "  -c  CSV file (default: $CSV_FILE)"
    echo "  -o  Output directory (default: $OUTPUT_DIR)"
    echo "  -m  Minimum trips (default: $MIN_TRIPS)"
    echo "  -p  Output file prefix (default: $OUTPUT_FILE_PREFIX)"
    echo "  -x  Enable octi (default: disabled)"
    echo "  -l  Colormap name (default: $COLORMAP)"
    echo "  -i  Important stops only (default: disabled)"
    echo "  -r  Hide routes (default: disabled)"
    echo "  -d  Direction (0 for down, 1 for up, default: $DIRECTION)"
    echo "  -s  Skip direction filter (default: disabled)"
    exit 1
}

# Parse command-line arguments
while getopts "g:t:c:o:m:p:xl:irsd:" opt; do
    case $opt in
        g) GTFS_FILE="$OPTARG" ;;
        t) IFS=' ' read -r -a STOP_IDS <<< "$OPTARG" ;;
        c) CSV_FILE="$OPTARG" ;;
        o) OUTPUT_DIR="$OPTARG" ;;
        m) MIN_TRIPS="$OPTARG" ;;
        p) OUTPUT_FILE_PREFIX="$OPTARG" ;;
        x) OCTI_ENABLED=true ;;
        l) COLORMAP="$OPTARG" ;;
        i) IMPORTANT_STOPS=true ;;
        r) HIDE_ROUTES=true ;;
        d) DIRECTION="$OPTARG" ;;
        s) SKIP_DIRECTION=true ;;
        *) usage ;;
    esac
done

# Check if GTFS file exists
if [ ! -f "$GTFS_FILE" ]; then
    echo "Error: GTFS file '$GTFS_FILE' not found."
    exit 1
fi

# Create the output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"



# Initialize an array to hold stop names
stop_names=()

echo "Starting GTFS processing..."

# Iterate over each stop ID to find corresponding stop names
for stop_id in "${STOP_IDS[@]}"; do
    # Use awk to find the stop_name corresponding to the stop_id
    stop_name=$(awk -F, -v id="$stop_id" '$4 == id {print $2}' "$CSV_FILE")
    
    # Add the stop name to the array if found
    if [ -n "$stop_name" ]; then
        stop_names+=("$stop_name")
        echo "Found stop name for ID $stop_id: $stop_name"
    else
        echo "Warning: Stop ID $stop_id not found in CSV."
    fi
done

# Function to sanitize filenames and limit length
sanitize_filename() {
    # First sanitize the string
    local sanitized=$(echo "$1" | sed -e 's/[/\\?%*:|"<>, ]/_/g' -e 's/__*/_/g' -e 's/^_//' -e 's/_$//')
    # Then truncate to 30 characters (adjust this number if needed)
    echo "${sanitized:0:30}"
}

# Join all stop names with underscores for the filename, with total length limit
sanitized_stop_names=""
max_total_length=100  # Adjust this value based on your system's limits
for name in "${stop_names[@]}"; do
    sanitized_name=$(sanitize_filename "$name")
    if [ -n "$sanitized_stop_names" ]; then
        # Check if adding this name would exceed the limit
        if [ ${#sanitized_stop_names} -lt $max_total_length ]; then
            sanitized_stop_names="${sanitized_stop_names}_${sanitized_name}"
        fi
    else
        sanitized_stop_names="$sanitized_name"
    fi
done

# Truncate the final string if it's still too long
sanitized_stop_names="${sanitized_stop_names:0:$max_total_length}"

# Define the output file names (update paths to include output directory)
OUTPUT_FILE="${OUTPUT_DIR}/${OUTPUT_FILE_PREFIX}_${sanitized_stop_names}.zip"
FINAL_MAP_GEOGRAPHIC="${OUTPUT_DIR}/${OUTPUT_FILE_PREFIX}_${sanitized_stop_names}_geographic.svg"
FINAL_MAP_SCHEMATIC="${OUTPUT_DIR}/${OUTPUT_FILE_PREFIX}_${sanitized_stop_names}_schematic.svg"

echo "Processing GTFS data for stop IDs: ${STOP_IDS[*]}"
echo "Output will be saved to:"
echo "  Geographic: $FINAL_MAP_GEOGRAPHIC"
echo "  Schematic: $FINAL_MAP_SCHEMATIC"

# Run the GTFS processing for all stop IDs at once, add viz_file name using final_map_file as template
python gtfs_process_cli.py "$GTFS_FILE" "${STOP_IDS[@]}" \
    --output-dir "$OUTPUT_DIR" \
    --min-trips "$MIN_TRIPS" \
    --output "${OUTPUT_FILE_PREFIX}_${sanitized_stop_names}.zip" \
    $([ "$IMPORTANT_STOPS" = true ] && echo "--important-stops-only") \
    $([ "$HIDE_ROUTES" = true ] && echo "--hide-routes") \
    --direction "$DIRECTION" \
    $([ "$SKIP_DIRECTION" = true ] && echo "--skip-direction-filter" ) \
    --viz-file "${sanitized_stop_names}.html"

# Check if the GTFS processing was successful
if [ $? -ne 0 ]; then
    echo "Error: GTFS processing failed. Please check the input file and parameters."
    exit 1
fi

# Verify the output file was created (now checking in the correct directory)
if [ ! -f "$OUTPUT_FILE" ]; then
    echo "Error: Output file '$OUTPUT_FILE' was not created."
    exit 1
fi

# Run the subsequent commands
gtfs2graph_cmd="gtfs2graph -m bus \"$OUTPUT_FILE\""
topo_cmd="topo"
color_geojson_cmd="python color_geojson_cli.py -c \"$COLORMAP\""
loom_cmd="loom --no-prune"

# Create temporary files in output directory
TEMP_BASE="${OUTPUT_DIR}/transitmap_base.json"
TEMP_OCTI="${OUTPUT_DIR}/transitmap_octi.json"

# Run base pipeline
echo "Running base preprocessing pipeline..."
eval "$gtfs2graph_cmd | $topo_cmd | $color_geojson_cmd | $loom_cmd > \"$TEMP_BASE\""

# Generate geographic map
echo "Generating geographic map..."

cat "$TEMP_BASE" | transitmap -l --station-label-textsize 100 > "$FINAL_MAP_GEOGRAPHIC"

# Generate schematic map with fresh pipeline
echo "Generating schematic map..."
# if [ "$OCTI_ENABLED" = true ]; then
    # eval "$gtfs2graph_cmd | $topo_cmd | $color_geojson_cmd | octi | $loom_cmd > \"$TEMP_OCTI\""
    # cat "$TEMP_OCTI" | transitmap -l --station-label-textsize 100 > "$FINAL_MAP_SCHEMATIC"
# else
cat "$TEMP_BASE" | octi | transitmap -l --station-label-textsize 100 > "$FINAL_MAP_SCHEMATIC"
# fi

# Check if both map generations were successful
if [ -f "$FINAL_MAP_GEOGRAPHIC" ] && [ -f "$FINAL_MAP_SCHEMATIC" ]; then
    echo "Successfully generated maps:"
    echo "  Geographic: $FINAL_MAP_GEOGRAPHIC"
    echo "  Schematic: $FINAL_MAP_SCHEMATIC"

    # Convert SVG files to PDF
    FINAL_MAP_GEOGRAPHIC_PDF="${FINAL_MAP_GEOGRAPHIC%.svg}.pdf"
    FINAL_MAP_SCHEMATIC_PDF="${FINAL_MAP_SCHEMATIC%.svg}.pdf"

    echo "Converting SVG files to PDF..."
    /Applications/Inkscape.app/Contents/MacOS/inkscape --export-filename="$FINAL_MAP_GEOGRAPHIC_PDF" --export-type=pdf "$FINAL_MAP_GEOGRAPHIC"
    /Applications/Inkscape.app/Contents/MacOS/inkscape --export-filename="$FINAL_MAP_SCHEMATIC_PDF" --export-type=pdf "$FINAL_MAP_SCHEMATIC"

    echo "PDF files generated:"
    echo "  Geographic PDF: $FINAL_MAP_GEOGRAPHIC_PDF"
    echo "  Schematic PDF: $FINAL_MAP_SCHEMATIC_PDF"
else
    echo "Error: One or both map generations failed."
    exit 1
fi