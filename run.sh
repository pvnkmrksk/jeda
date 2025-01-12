#!/bin/bash

# Default values for variables
GTFS_FILE="bmtc-2.zip"
CSV_FILE="stop_trip_counts.csv"
OUTPUT_DIR="output"
MIN_TRIPS=5
OUTPUT_FILE_PREFIX="BMTC_transit"
OCTI_ENABLED=false
COLORMAP="tab20c"
IMPORTANT_STOPS=false
HIDE_ROUTES=false
DIRECTION=0
SKIP_DIRECTION=false
# Define the list of stop IDs you want to process
STOP_IDS=("5wx" "32p")
# Add force flag to default variables section
FORCE_REBUILD=false
# Function to display usage
usage() {
    echo "Usage: $0 [-g gtfs_file] [-c csv_file] [-o output_dir] [-m min_trips] [-p output_file_prefix] [-x] [-l colormap] [-i] [-r] [-d direction] [-s] [-f]"
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
    echo "  -f  Force rebuild all steps (default: disabled)"
    exit 1
}

# Parse command-line arguments
while getopts "g:t:c:o:m:p:xl:irsd:f" opt; do
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
        f) FORCE_REBUILD=true ;;
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
stop_ids_string=$(IFS=_ ; echo "${STOP_IDS[*]}")  # Join stop IDs with underscore
max_total_length=50  # Reduced length limit for better compatibility

# Create a shorter version of stop names
for name in "${stop_names[@]}"; do
    sanitized_name=$(sanitize_filename "$name" | cut -c1-15)  # Limit each name to 15 chars
    if [ -n "$sanitized_stop_names" ]; then
        sanitized_stop_names="${sanitized_stop_names}_${sanitized_name}"
    else
        sanitized_stop_names="$sanitized_name"
    fi
done

# Create base filename without extension
BASE_FILENAME="${OUTPUT_DIR}/${OUTPUT_FILE_PREFIX}_${stop_ids_string}_m${MIN_TRIPS}_${sanitized_stop_names}"

# Define the output file names
OUTPUT_FILE="${BASE_FILENAME}.zip"
FINAL_MAP_GEOGRAPHIC="${BASE_FILENAME}_geographic.svg"
FINAL_MAP_SCHEMATIC="${BASE_FILENAME}_schematic.svg"

echo "Processing GTFS data for stop IDs: ${STOP_IDS[*]}"
echo "Output will be saved to:"
echo "  Geographic: $FINAL_MAP_GEOGRAPHIC"
echo "  Schematic: $FINAL_MAP_SCHEMATIC"

# Before running GTFS processing, check if output file already exists
if need_processing "$OUTPUT_FILE"; then
    echo "Processing GTFS data for stop IDs: ${STOP_IDS[*]}"
    echo "Output will be saved to:"
    echo "  Geographic: $FINAL_MAP_GEOGRAPHIC"
    echo "  Schematic: $FINAL_MAP_SCHEMATIC"

    # Run the GTFS processing for all stop IDs at once
    python gtfs_process_cli.py "$GTFS_FILE" "${STOP_IDS[@]}" \
        --output-dir "$OUTPUT_DIR" \
        --min-trips "$MIN_TRIPS" \
        --output "${OUTPUT_FILE_PREFIX}_${stop_ids_string}_m${MIN_TRIPS}_${sanitized_stop_names}.zip" \
        $([ "$IMPORTANT_STOPS" = true ] && echo "--important-stops-only") \
        $([ "$HIDE_ROUTES" = true ] && echo "--hide-routes") \
        --direction "$DIRECTION" \
        $([ "$SKIP_DIRECTION" = true ] && echo "--skip-direction-filter" ) \
        --viz-file "${stop_ids_string}_m${MIN_TRIPS}_${sanitized_stop_names}.html"

    # Check if the GTFS processing was successful
    if [ $? -ne 0 ]; then
        echo "Error: GTFS processing failed. Please check the input file and parameters."
        exit 1
    fi

    # Verify the output file was created
    if [ ! -f "$OUTPUT_FILE" ]; then
        echo "Error: Output file '$OUTPUT_FILE' was not created."
        exit 1
    fi
else
    echo "Using existing GTFS subset file: $OUTPUT_FILE"
fi

# Run the subsequent commands
gtfs2graph_cmd="gtfs2graph -m bus \"$OUTPUT_FILE\""
topo_cmd="topo"
color_geojson_cmd="python color_geojson_cli.py -c \"$COLORMAP\""
loom_cmd="loom --no-prune"

# Create temporary files in output directory
TEMP_BASE="${OUTPUT_DIR}/transitmap_base.json"
TEMP_OCTI="${OUTPUT_DIR}/transitmap_octi.json"

# Rename temp files to follow same naming convention
BASE_GRAPH="${BASE_FILENAME}_base_graph.json"
BASE_TOPO="${BASE_FILENAME}_base_topo.json"
BASE_COLORED="${BASE_FILENAME}_base_colored.json"
BASE_LOOMED="${BASE_FILENAME}_base_loomed.json"
SCHEMATIC_OCTI="${BASE_FILENAME}_schematic_octi.json"

# Function to check if processing is needed
need_processing() {
    local output_file="$1"
    if [ "$FORCE_REBUILD" = true ] || [ ! -f "$output_file" ]; then
        return 0  # true, processing needed
    else
        return 1  # false, processing not needed
    fi
}

# Run base pipeline with checks for each step
echo "Running preprocessing pipeline..."

if need_processing "$BASE_GRAPH"; then
    echo "Generating base graph..."
    eval "$gtfs2graph_cmd > \"$BASE_GRAPH\""
fi

if need_processing "$BASE_TOPO"; then
    echo "Running topology processing..."
    cat "$BASE_GRAPH" | eval "$topo_cmd > \"$BASE_TOPO\""
fi

if need_processing "$BASE_COLORED"; then
    echo "Applying colors..."
    cat "$BASE_TOPO" | eval "$color_geojson_cmd > \"$BASE_COLORED\""
fi

if need_processing "$BASE_LOOMED"; then
    echo "Running loom processing..."
    cat "$BASE_COLORED" | eval "$loom_cmd > \"$BASE_LOOMED\""
fi

# Generate geographic map
echo "Generating geographic map..."
if need_processing "$FINAL_MAP_GEOGRAPHIC"; then
    cat "$BASE_LOOMED" | transitmap -l --station-label-textsize 100 > "$FINAL_MAP_GEOGRAPHIC"
fi

# Generate schematic map
echo "Generating schematic map..."
if need_processing "$SCHEMATIC_OCTI"; then
    cat "$BASE_LOOMED" | octi > "$SCHEMATIC_OCTI"
fi

if need_processing "$FINAL_MAP_SCHEMATIC"; then
    cat "$SCHEMATIC_OCTI" | transitmap -l --station-label-textsize 100 > "$FINAL_MAP_SCHEMATIC"
fi

# Add SVG and PDF files to the need_processing check
FINAL_MAP_GEOGRAPHIC_ADJUSTED="${BASE_FILENAME}_geographic_adjusted.svg"
FINAL_MAP_SCHEMATIC_ADJUSTED="${BASE_FILENAME}_schematic_adjusted.svg"
FINAL_MAP_GEOGRAPHIC_PDF="${FINAL_MAP_GEOGRAPHIC%.svg}.pdf"
FINAL_MAP_SCHEMATIC_PDF="${FINAL_MAP_SCHEMATIC%.svg}.pdf"

# Replace the SVG adjustment and PDF conversion section with:
if [ -f "$FINAL_MAP_GEOGRAPHIC" ] && [ -f "$FINAL_MAP_SCHEMATIC" ]; then
    echo "Successfully generated maps:"
    echo "  Geographic: $FINAL_MAP_GEOGRAPHIC"
    echo "  Schematic: $FINAL_MAP_SCHEMATIC"

    # Adjust SVG files
    if need_processing "$FINAL_MAP_GEOGRAPHIC_ADJUSTED"; then
        echo "Adjusting geographic SVG..."
        python3 "$OUTPUT_DIR/adjust_svg.py" "$FINAL_MAP_GEOGRAPHIC" "$FINAL_MAP_GEOGRAPHIC_ADJUSTED" 0.85
    fi

    if need_processing "$FINAL_MAP_SCHEMATIC_ADJUSTED"; then
        echo "Adjusting schematic SVG..."
        python3 "$OUTPUT_DIR/adjust_svg.py" "$FINAL_MAP_SCHEMATIC" "$FINAL_MAP_SCHEMATIC_ADJUSTED" 0.85
    fi

    # Convert SVG files to PDF
    if need_processing "$FINAL_MAP_GEOGRAPHIC_PDF"; then
        echo "Converting geographic SVG to PDF..."
        /Applications/Inkscape.app/Contents/MacOS/inkscape --export-filename="$FINAL_MAP_GEOGRAPHIC_PDF" \
            --export-type=pdf "$FINAL_MAP_GEOGRAPHIC_ADJUSTED"
    fi

    if need_processing "$FINAL_MAP_SCHEMATIC_PDF"; then
        echo "Converting schematic SVG to PDF..."
        /Applications/Inkscape.app/Contents/MacOS/inkscape --export-filename="$FINAL_MAP_SCHEMATIC_PDF" \
            --export-type=pdf "$FINAL_MAP_SCHEMATIC_ADJUSTED"
    fi

    echo "Files generated:"
    echo "  Geographic SVG: $FINAL_MAP_GEOGRAPHIC_ADJUSTED"
    echo "  Schematic SVG: $FINAL_MAP_SCHEMATIC_ADJUSTED"
    echo "  Geographic PDF: $FINAL_MAP_GEOGRAPHIC_PDF"
    echo "  Schematic PDF: $FINAL_MAP_SCHEMATIC_PDF"
else
    echo "Error: One or both map generations failed."
    exit 1
fi