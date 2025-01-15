[![2015 Stuttgart light rail network maps generated from GTFS data, with optimal line orderings, geographically correct (left), octilinear (middle), and  orthoradial (right).](examples/render/stuttgart-example-small.png?raw=true)](examples/render/stuttgart-example.png?raw=true)
*2015 Stuttgart light rail network maps generated from GTFS data, with optimal line orderings, geographically correct (left), octilinear (middle), and  orthoradial (right).*

[![Build](https://github.com/ad-freiburg/loom/actions/workflows/build.yml/badge.svg)](https://github.com/ad-freiburg/loom/actions/workflows/build.yml)

LOOM
====

Software suite for the automated generation of geographically correct or schematic transit maps.

Based on our work in the following papers:
[Bast H., Brosi P., Storandt S., Efficient Generation of Geographically Accurate Transit Maps, SIGSPATIAL 2018](http://ad-publications.informatik.uni-freiburg.de/SIGSPATIAL_transitmaps_2018.pdf)
[Bast H., Brosi P., Storandt S., Efficient Generation of Geographically Accurate Transit Maps (extended version), ACM TSAS, Vol. 5, No. 4, Article 25, 2019](http://ad-publications.informatik.uni-freiburg.de/ACM_efficient%20Generation%20of%20%20Geographically%20Accurate%20Transit%20Maps_extended%20version.pdf)
[Bast H., Brosi P., Storandt S., Metro Maps on Octilinear Grid Graphs, EuroVis 2020](http://ad-publications.informatik.uni-freiburg.de/EuroVis%20octi-maps.pdf)
[Bast H., Brosi P., Storandt S., Metro Maps on Flexible Base Grids, SSTD 2021](http://ad-publications.informatik.uni-freiburg.de/SSTD_Metro%20Maps%20on%20Flexible%20Base%20Grids.pdf).
A pipeline for generating geographically accurate transit maps which appears to be similar to ours was described by Anton Dubrau in a [blog post](https://blog.transitapp.com/how-we-built-the-worlds-prettiest-auto-generated-transit-maps-12d0c6fa502f).

Also see our web demos [here](https://loom.cs.uni-freiburg.de/), [here](https://loom.cs.uni-freiburg.de/global), and [here](https://octi.cs.uni-freiburg.de).

Requirements
------------

 * `cmake`
 * `gcc >= 5.0` (or `clang >= 3.9`)
 * Optional: `libglpk-dev`, `coinor-libcbc-dev`, `gurobi`, `libzip-dev`, `libprotobuf-dev`


Building and Installation
-------------------------

Fetch this repository and init submodules:

```
git clone --recurse-submodules https://github.com/ad-freiburg/loom.git
```

Build and install:

```
cd loom
mkdir build && cd build
cmake ..
make -j
```

To (optionally) install, type
```
make install
```

You can also use the binaries in `./build` directly.

Usage
=====

This suite consists of several tools:

* `gtfs2graph`, create a GeoJSON line graph from GTFS data
* `topo`, create an overlapping-free line graph from an arbitrary line graph
* `loom`, find optimal line orderings on a line graph
* `octi`, create a schematic version of a line graph
* `transitmap`, render a line graph into an SVG map (`--render-engine=svg`) or into vector tiles (`--render-engine=mvt`)

All tools output a graph, in the GeoJSON format, to `stdout`, and expect a GeoJSON graph at `stdin`. Exceptions are `gtfs2graph`, where the input is a GTFS feed, and `transitmap`, which writes SVG to `stdout` or MVT vector tiles to a specified folder.

The `example` folder contains several overlapping-free line graphs.

To render the geographically correct Stuttgart map from above, use
```
cat examples/stuttgart.json | loom | transitmap > stuttgart.svg
```

To also render labels, use

```
cat examples/stuttgart.json | loom | transitmap -l > stuttgart-label.svg
```

To render an *octilinear* map, put the `octi` tool into the pipe:

```
cat examples/stuttgart.json | loom | octi | transitmap -l > stuttgart-octilin.svg
```

To render for example the orthoradial map from above, use a different base graph for `octi`:

```
cat examples/stuttgart.json | loom | octi -b orthoradial | transitmap -l > stuttgart-orthorad.svg
```

Line graph extraction from GTFS
-------------------------------

To extract for example a line graph for streetcars from GTFS data, use `gtfs2graph` as follows:

```
gtfs2graph -m tram freiburg.zip > freiburg.json
```

This line graph will have many overlapping edges and stations. To create an overlapping-free line graph ready for rendering, add `topo`:

```
gtfs2graph -m tram freiburg.zip | topo > freiburg.json
```

A full pipeline for creating an octilinear map of the Freiburg tram network would look like this:
```
gtfs2graph -m tram freiburg.zip | topo | loom | octi | transitmap > freiburg-tram.svg
```

Usage via Docker
================

You can also use any tool in a Docker container via the provided Dockerfile.

To build the container:

```
docker build -t loom
```

To run a tool from the suite, use

```
docker run -i loom <TOOL>
```

For example, to octilinearize the Freiburg example, use

```
cat examples/freiburg.json | sudo docker run -i loom octi
```

*Note*: if you want to use gurobi for ILP optimization, you *must* mount a folder container a valid gurobi license file `gurobi.lic` to `/gurobi/` in the container. For example, if your `gurobi.lic` is in `/home/user/gurobi`:

```
docker run -v /home/user/gurobi:/gurobi loom <TOOL>
```

New Script Abilities and Typical Pipelines
------------------------------------------

The `process_transit_map.sh` script automates the generation of transit maps from GTFS data. It supports various parameters for customization, such as:

- `--stops` or `-s`: Comma-separated stop IDs
- `--routes` or `-r`: Route number pattern
- `--min-trips` or `-m`: Minimum trips per route (default: 15)
- `--max-dist` or `-d`: Maximum aggregation distance in meters (default: 150)
- `--smooth` or `-sm`: Smoothing value (default: 20)
- `--output-dir` or `-o`: Output directory (default: output)
- `--line-width` or `-w`: Line width (default: 20)
- `--line-spacing` or `-sp`: Line spacing (default: 10)
- `--outline-width` or `-ow`: Width of line outlines (default: 1)
- `--station-label-size` or `-sl`: Station label text size (default: 60)
- `--line-label-size` or `-ll`: Line label text size (default: 40)
- `--padding` or `-p`: Padding, -1 for auto (default: -1)
- `--text-shrink` or `-ts`: Text shrink percentage (default: 0.90)
- `--verbose` or `-v`: Enable debug mode with verbose output

Example Usage
-------------

To generate a transit map with default settings:

```bash
./process_transit_map.sh bmtc-2.zip
```

To specify stops and routes:

```bash
./process_transit_map.sh bmtc-2.zip --stops "3ie,sw" --routes "1,2,3"
```

To enable verbose output:

```bash
./process_transit_map.sh bmtc-2.zip --verbose
```

Standard Header
---------------

This project is licensed under a license respecting the original work it was derived from.

ಪವನ ಕುಮಾರ ​| Pavan Kumar, PhD
@pvnkmrksk

Extended Pipeline Tools
----------------------

In addition to the core LOOM tools, this fork provides additional scripts for automated transit map generation and processing:

### Process Transit Map Script (`process_transit_map.sh`)

A comprehensive shell script that automates the entire pipeline from GTFS data to final SVG maps. The script handles:
- GTFS subsetting and filtering
- Geographic and schematic map generation
- Automatic text size adjustment
- Output organization

#### Basic Usage

```bash
./process_transit_map.sh <gtfs_file.zip>
```

This will generate both geographic and schematic maps with default settings in the `output` directory.

#### Common Use Cases

1. Filter specific stops and routes:
```bash
./process_transit_map.sh input.zip --stops "stop1,stop2" --routes "1,2,3"
```

2. Adjust map appearance:
```bash
./process_transit_map.sh input.zip --line-width 25 --station-label-size 70
```

#### Pipeline Steps

The script executes the following steps:
1. GTFS subsetting: `gtfs_subset_cli.py` filters the input GTFS
2. Graph generation: `gtfs2graph` converts GTFS to graph format
3. Topology processing: `topo` handles overlapping edges
4. Line ordering: `loom` optimizes line arrangements
5. Map generation: `transitmap` creates the final SVG
6. Post-processing: Adjusts text sizes and spacing

#### Advanced Parameters

Common parameters:
- `--min-trips (-m)`: Minimum trips per route (default: 15)
- `--max-dist (-d)`: Maximum aggregation distance (default: 150m)
- `--smooth (-sm)`: Smoothing factor (default: 20)

Visual customization:
- `--line-width (-w)`: Line width (default: 20)
- `--line-spacing (-sp)`: Space between lines (default: 10)
- `--station-label-size (-sl)`: Station text size (default: 60)
- `--line-label-size (-ll)`: Line number text size (default: 40)
- `--text-shrink (-ts)`: Text adjustment factor (default: 0.90)

Output control:
- `--output-dir (-o)`: Output directory (default: output)
- `--verbose (-v)`: Enable detailed logging

License and Attribution
----------------------

This work is derived from the LOOM project and is licensed under the same terms as the original work.
See the original papers and citations above for the foundational research.

Extended functionality and automation scripts contributed by:
ಪವನ ಕುಮಾರ ​| Pavan Kumar, PhD
@pvnkmrksk
