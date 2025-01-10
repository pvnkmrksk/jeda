#!/usr/bin/env python3

import sys
import json
import matplotlib.pyplot as plt
import natsort
import argparse

def process_geojson(geojson_data, colormap_name='magma'):
    """Process GeoJSON data by assigning unique colors to each line based on labels."""
    
    # Extract 'label' values and sort them naturally
    labels = []
    for feature in geojson_data['features']:
        if 'lines' in feature['properties']:
            for line in feature['properties']['lines']:
                if 'label' in line:
                    labels.append(line['label'])

    # Remove duplicates and sort naturally
    labels = list(set(labels))
    labels = natsort.natsorted(labels)
    
    # Assign colors using the specified colormap
    num_labels = len(labels)
    colormap = plt.get_cmap(colormap_name)
    colors = [colormap(i / num_labels) for i in range(num_labels)]
    hex_colors = ['#' + ''.join([f'{int(c*255):02x}' for c in color[:3]]) for color in colors]

    # Map labels to colors
    label_color_map = dict(zip(labels, hex_colors))

    # Assign colors to each line in the GeoJSON
    for feature in geojson_data['features']:
        if 'lines' in feature['properties']:
            for line in feature['properties']['lines']:
                if 'label' in line:
                    line['color'] = label_color_map.get(line['label'], '')

    return geojson_data

def main():
    parser = argparse.ArgumentParser(description='Assign colors to GeoJSON features')
    parser.add_argument('-c', '--colormap', default='magma',
                      help='Matplotlib colormap name (default: magma)')
    args = parser.parse_args()

    # Read from stdin
    input_data = json.load(sys.stdin)
    
    # Process the data
    output_data = process_geojson(input_data, args.colormap)
    
    # Write to stdout
    json.dump(output_data, sys.stdout)

if __name__ == "__main__":
    main()
