#!/bin/bash

# Logging functions
log_section() {
    if [ "$DEBUG" = true ]; then
        echo -e "\n=== $1 ===\n"
    else
        echo -e "\n→ $1"
    fi
}

log_info() {
    if [ "$DEBUG" = true ]; then
        echo "INFO: $1"
    else
        echo "- $1"
    fi
}

log_cmd() {
    if [ "$DEBUG" = true ]; then
        echo -e "\nCommand to execute:"
        echo "$ $1"
    fi
}

log_error() {
    echo "ERROR: $1" >&2
}

print_output_tree() {
    local basename="$1"
    local output_dir="$2"
    
    echo -e "\nOutput files in $output_dir/:"
    echo "├── GTFS Subset:"
    echo "│   └── ${basename}.zip"
    echo "├── Intermediate Files:"
    echo "│   └── ${basename}_loom.json"
    echo "└── Final Maps:"
    echo "    ├── Geographic Maps:"
    echo "    │   ├── ${basename}_geographic.svg"
    echo "    │   └── ${basename}_geographic_adjusted.svg"
    echo "    └── Schematic Maps:"
    echo "        ├── ${basename}_schematic.svg"
    echo "        └── ${basename}_schematic_adjusted.svg"
}

# Default values
STOPS=""
ROUTES=""
MIN_TRIPS=15
MAX_AGGR_DIST=150
SMOOTHING=20
OUTPUT_DIR="output"
LINE_WIDTH=20
LINE_SPACING=10
OUTLINE_WIDTH=1
STATION_LABEL_SIZE=60
LINE_LABEL_SIZE=40
PADDING=-1
TEXT_SHRINK=0.85  # Default text shrink percentage
DEBUG=false

# Parse command line arguments
POSITIONAL_ARGS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        --stops|-s)
            STOPS="$2"
            shift 2
            ;;
        --routes|-r)
            ROUTES="$2"
            shift 2
            ;;
        --min-trips|-m)
            MIN_TRIPS="$2"
            shift 2
            ;;
        --max-dist|-d)
            MAX_AGGR_DIST="$2"
            shift 2
            ;;
        --smooth|-sm)
            SMOOTHING="$2"
            shift 2
            ;;
        --output-dir|-o)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --line-width|-w)
            LINE_WIDTH="$2"
            shift 2
            ;;
        --line-spacing|-sp)
            LINE_SPACING="$2"
            shift 2
            ;;
        --outline-width|-ow)
            OUTLINE_WIDTH="$2"
            shift 2
            ;;
        --station-label-size|-sl)
            STATION_LABEL_SIZE="$2"
            shift 2
            ;;
        --line-label-size|-ll)
            LINE_LABEL_SIZE="$2"
            shift 2
            ;;
        --padding|-p)
            PADDING="$2"
            shift 2
            ;;
        --text-shrink|-ts)
            TEXT_SHRINK="$2"
            shift 2
            ;;
        --verbose|-v)
            DEBUG=true
            shift
            ;;
        *)
            POSITIONAL_ARGS+=("$1")
            shift
            ;;
    esac
done

# Restore positional arguments
set -- "${POSITIONAL_ARGS[@]}"

# Check if GTFS file is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <gtfs.zip> [options]"
    echo "Options:"
    echo "  --stops, -s              : Comma-separated stop IDs"
    echo "  --routes, -r             : Route number pattern"
    echo "  --min-trips, -m          : Minimum trips per route (default: 15)"
    echo "  --max-dist, -d           : Maximum aggregation distance (default: 150)"
    echo "  --smooth, -sm            : Smoothing value (default: 20)"
    echo "  --output-dir, -o         : Output directory (default: output)"
    echo "  --line-width, -w         : Line width (default: 20)"
    echo "  --line-spacing, -sp      : Line spacing (default: 10)"
    echo "  --outline-width, -ow     : Width of line outlines (default: 1)"
    echo "  --station-label-size, -sl: Station label text size (default: 60)"
    echo "  --line-label-size, -ll   : Line label text size (default: 40)"
    echo "  --padding, -p            : Padding, -1 for auto (default: -1)"
    echo "  --text-shrink, -ts        : Text shrink percentage (default: 0.85)"
    echo "  --debug, -d              : Enable debug mode with verbose output"
    exit 1
fi

GTFS_FILE=$1

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Run gtfs_subset_cli.py and capture its output (which is the generated filename)
SUBSET_CMD="python gtfs_subset_cli.py $GTFS_FILE"
if [ ! -z "$STOPS" ]; then
    # Remove all spaces from the stops list
    STOPS=$(echo "$STOPS" | tr -d ' ')
    SUBSET_CMD="$SUBSET_CMD --stops $STOPS"
fi
if [ ! -z "$ROUTES" ]; then
    # Remove all spaces from the routes list
    ROUTES=$(echo "$ROUTES" | tr -d ' ')
    SUBSET_CMD="$SUBSET_CMD --routes $ROUTES"
fi
if [ ! -z "$MIN_TRIPS" ]; then
    SUBSET_CMD="$SUBSET_CMD --min-trips $MIN_TRIPS"
fi

log_section "Processing GTFS"
log_cmd "$SUBSET_CMD"
if ! SUBSET_GTFS=$(eval "$SUBSET_CMD" 2>&1 | tail -n 1); then
    log_error "Failed to create GTFS subset"
    exit 1
fi

# Extract basename and move file to output dir
BASENAME=$(basename "$SUBSET_GTFS" .zip)
if [ ! -d "$OUTPUT_DIR" ]; then
    mkdir -p "$OUTPUT_DIR"
fi
mv -f "$SUBSET_GTFS" "$OUTPUT_DIR/"
SUBSET_GTFS="$OUTPUT_DIR/$(basename $SUBSET_GTFS)"

log_info "Created GTFS subset"
log_info "Output: ${BASENAME}.zip"

# Common parameters for transitmap
COMMON_PARAMS="--line-width $LINE_WIDTH \
    --line-spacing $LINE_SPACING \
    --outline-width $OUTLINE_WIDTH \
    --station-label-textsize $STATION_LABEL_SIZE \
    --line-label-textsize $LINE_LABEL_SIZE \
    --padding $PADDING \
    --labels \
    --tight-stations \
    --render-dir-markers"

# Run common pipeline once and save intermediate result
log_section "Generating Maps"
log_cmd "$PIPELINE_CMD"
LOOM_JSON="$OUTPUT_DIR/${BASENAME}_loom.json"
PIPELINE_CMD="gtfs2graph -m bus $SUBSET_GTFS | topo --smooth $SMOOTHING -d $MAX_AGGR_DIST | loom > $LOOM_JSON"
eval "$PIPELINE_CMD"
log_info "Created intermediate file: ${BASENAME}_loom.json"

# Generate geographic map from loom output
log_info "Generating geographic map"
GEOGRAPHIC_CMD="cat $LOOM_JSON | transitmap $COMMON_PARAMS > $OUTPUT_DIR/${BASENAME}_geographic.svg"
log_cmd "$GEOGRAPHIC_CMD"
eval "$GEOGRAPHIC_CMD"
log_info "Created: ${BASENAME}_geographic.svg"

# Generate schematic map from loom output
log_info "Generating schematic map"
SCHEMATIC_CMD="cat $LOOM_JSON | octi | transitmap $COMMON_PARAMS > $OUTPUT_DIR/${BASENAME}_schematic.svg"
log_cmd "$SCHEMATIC_CMD"
eval "$SCHEMATIC_CMD"
log_info "Created: ${BASENAME}_schematic.svg"

# Create adjusted SVG files with shrunk text
log_section "Post-Processing"
log_info "Adjusting text sizes"
GEOGRAPHIC_ADJUSTED="${OUTPUT_DIR}/${BASENAME}_geographic_adjusted.svg"
SCHEMATIC_ADJUSTED="${OUTPUT_DIR}/${BASENAME}_schematic_adjusted.svg"

python3 adjust_svg.py "$OUTPUT_DIR/${BASENAME}_geographic.svg" "$GEOGRAPHIC_ADJUSTED" "$TEXT_SHRINK"
log_info "Created: ${BASENAME}_geographic_adjusted.svg"
python3 adjust_svg.py "$OUTPUT_DIR/${BASENAME}_schematic.svg" "$SCHEMATIC_ADJUSTED" "$TEXT_SHRINK"
log_info "Created: ${BASENAME}_schematic_adjusted.svg"

# Print final output tree
log_section "Summary"
print_output_tree "$BASENAME" "$OUTPUT_DIR" 