# Magga (ಮಗ್ಗ/मग्ग)

[![Build](https://github.com/pvnkmrksk/magga/actions/workflows/build.yml/badge.svg)](https://github.com/pvnkmrksk/magga/actions/workflows/build.yml)

A toolkit for weaving transit data into beautiful, meaningful maps.

## About Magga

"Magga" carries dual meaning - a loom (ಮಗ್ಗ) in Kannada that weaves intricate patterns, and "path" (मग्ग) in Pali Buddhism, referring to the noble path to enlightenment. This duality perfectly captures our mission: just as a loom weaves threads into beautiful patterns, we weave transit routes into readable maps. And just as the Noble Eightfold Path guides beings toward enlightenment, accessible public transit guides communities toward sustainability and equity.

In cities where most of humanity now lives and where the majority of CO2 emissions occur, public transit serves as a crucial path toward:
- Reducing environmental impact and fighting climate change
- Connecting people to opportunities and lifting communities from poverty
- Creating more livable, sustainable urban spaces
- Weaving the social fabric that binds communities together

## Features

- Generate both geographic and schematic transit maps
- Interactive visualization tools for exploring transit networks
- Flexible filtering and subsetting of GTFS data
- Customizable styling and appearance
- Automated text size adjustment for optimal readability
- Support for various transit modes (bus, tram, rail, etc.)

## Quick Start

### Installation

```bash
git clone --recurse-submodules https://github.com/pvnkmrksk/magga.git
cd magga
mkdir build && cd build
cmake ..
make -j
```

Optionally install system-wide:
```bash
make install
```

### Basic Usage

Generate a transit map from GTFS data:
```bash
./process_transit_map.sh input.zip
```

Filter specific routes and stops:
```bash
./process_transit_map.sh input.zip --stops "stop1,stop2" --routes "1,2,3"
```

Create an interactive web visualization:
```bash
python gtfs_map_viewer.py input.zip
```

### Manual Pipeline

For more control, you can run the pipeline tools individually:

```bash
# Create a filtered subset of GTFS data
python gtfs_subset_cli.py input.zip --stops "3ie,sw" -m 15 -o subset.zip

# Generate maps using the pipeline
gtfs2graph -m bus subset.zip | \
    topo --smooth 20 -d 150 | \
    loom | \
    octi | \
    transitmap -l --tight-stations --render-dir-markers > output.svg

# For geographic maps, skip octilinearization
gtfs2graph -m bus subset.zip | \
    topo --smooth 20 -d 150 | \
    loom | \
    transitmap -l --tight-stations --render-dir-markers > geographic.svg
```

Each step in the pipeline serves a specific purpose:
- `gtfs2graph`: Converts GTFS to a graph format
- `topo`: Handles overlapping edges and station clustering
- `loom`: Optimizes line arrangements
- `octi`: Creates schematic (octilinear) layouts
- `transitmap`: Renders the final SVG with labels and styling

## Tools Overview

### process_transit_map.sh
The main pipeline tool that automates the entire process from GTFS to final maps. It handles:
- GTFS subsetting and filtering
- Geographic and schematic map generation
- Automatic text size adjustment
- Output organization

### gtfs_subset_cli.py
A tool for creating focused subsets of GTFS data based on:
- Specific stops or routes
- Minimum trip counts
- Pattern matching for route names

### gtfs_map_viewer.py
Interactive web visualization tool featuring:
- Route visualization with frequency-based styling
- Stop visualization with customizable metrics
- Detailed information popups
- Multiple color scheme options

### adjust_svg.py
Post-processing tool for optimizing text sizes and spacing in generated maps.

## Requirements

Core requirements:
* `cmake`
* `gcc >= 5.0` (or `clang >= 3.9`)
* Python 3.6+

Optional dependencies for enhanced functionality:
* `libglpk-dev`
* `coinor-libcbc-dev`
* `gurobi`
* `libzip-dev`
* `libprotobuf-dev`

## Docker Usage

You can also use the tools via Docker:

```bash
docker build -t magga .
docker run -i magga <TOOL>
```

For Gurobi optimization, mount your license:
```bash
docker run -v /path/to/gurobi:/gurobi magga <TOOL>
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.

## Acknowledgments

This work builds upon the foundational research and implementation of the LOOM project by Hannah Bast, Patrick Brosi, and Sabine Storandt. Their groundbreaking work in transit map generation is documented in:

- [Efficient Generation of Geographically Accurate Transit Maps](http://ad-publications.informatik.uni-freiburg.de/SIGSPATIAL_transitmaps_2018.pdf) (SIGSPATIAL 2018)
- [Metro Maps on Octilinear Grid Graphs](http://ad-publications.informatik.uni-freiburg.de/EuroVis%20octi-maps.pdf) (EuroVis 2020)
- [Metro Maps on Flexible Base Grids](http://ad-publications.informatik.uni-freiburg.de/SSTD_Metro%20Maps%20on%20Flexible%20Base%20Grids.pdf) (SSTD 2021)

We are grateful to stand on the shoulders of these giants in our mission to make transit networks more accessible and understandable.

## Author

ಪವನ ಕುಮಾರ ​| Pavan Kumar, PhD  
[@pvnkmrksk](https://github.com/pvnkmrksk)

## TODO

### Name Processing
- [ ] Procedural name shortening
  - Implement intelligent abbreviation rules for common words (Street → St, Road → Rd)
  - Handle multilingual name variants
  - Preserve uniqueness while shortening
  - Configure maximum name length threshold

### Stop Consolidation
- [ ] Lat-long based stop merging
  - Merge stops with identical names within configurable distance threshold
  - Preserve all stop IDs for routing purposes
  - Calculate centroid for merged stop placement
  - Handle edge cases with partial name matches

### Subsetting Features
- [ ] Distance-based network subsetting
  - Implement radius-based filtering from focus stop(s)
  - Support multiple foci with union/intersection options
  - Include connecting routes between included stops
  - Preserve network connectivity

### Route Filtering
- [ ] Pattern-based route exclusion
  - Support glob patterns for route exclusion (e.g., "Night*", "X*")
  - Allow regex patterns for complex matching
  - Implement whitelist/blacklist functionality
  - Preserve route dependencies

### Major Junction Handling
- [ ] Junction detection and labeling
  - Identify major junctions based on:
    - Number of intersecting routes
    - Passenger volume/frequency
    - Geographic importance
  - Smart label placement for major junctions
  - Configurable importance thresholds
  - Option to show only major junction labels

### Map Visualization
- [ ] Junction-focused display
  - Implement toggle for junction-only view
  - Scale junction markers by importance
  - Smart label density control
  - Maintain visual hierarchy
