import pandas as pd
import folium
from pathlib import Path
import zipfile
import tempfile
import os
import sys
from branca.colormap import LinearColormap
import numpy as np
import matplotlib.pyplot as plt  # For colormaps
from matplotlib.colors import LinearSegmentedColormap, to_hex

class GTFSMapCreator:
    """
    Create interactive HTML maps from GTFS data with customizable visualizations.

    Example usage:
        # Basic usage
        creator = GTFSMapCreator("input.zip")
        creator.load_gtfs_data()
        creator.create_map("output.html")
        
        # Show only stops
        creator.create_map("stops_only.html", stops_only=True)
        
        # Color stops by route count
        creator.create_map(
            "routes_map.html",
            color_by='routes',
            cmap='viridis'
        )
        
        # Custom coloring for both stops and routes
        creator.create_map(
            "custom_map.html",
            color_by='trips',
            cmap='YlOrRd',      # Yellow-Orange-Red colormap for stops
            route_cmap='Blues'   # Blue colormap for routes
        )

    Command-line usage:
        # Basic map
        python gtfs_map_viewer.py input.zip
        
        # Custom output with route coloring
        python gtfs_map_viewer.py input.zip --output map.html --cmap viridis --route-cmap magma
        
        # Color by route count
        python gtfs_map_viewer.py input.zip --color-by routes --cmap YlOrRd
        
        # Stops only
        python gtfs_map_viewer.py input.zip --stops-only
    """

    def __init__(self, gtfs_path):
        self.gtfs_path = gtfs_path
        self.stops_df = None
        self.routes_df = None
        self.trips_df = None
        self.stop_times_df = None
        self.shapes_df = None
        
    def validate_gtfs_file(self):
        """Validate if the file is a valid GTFS zip and contains required files"""
        try:
            with zipfile.ZipFile(self.gtfs_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                stops_file = next((f for f in file_list if f.lower().endswith('stops.txt')), None)
                return bool(stops_file)
        except Exception as e:
            print(f"Error validating GTFS file: {str(e)}")
            return False

    def load_gtfs_data(self):
        """Load required GTFS files into pandas dataframes"""
        if not self.validate_gtfs_file():
            sys.exit(1)

        try:
            with zipfile.ZipFile(self.gtfs_path, 'r') as zip_ref:
                with tempfile.TemporaryDirectory() as tmpdir:
                    zip_ref.extractall(tmpdir)
                    
                    # Find stops.txt recursively
                    stops_path = next(Path(tmpdir).rglob('stops.txt'))
                    gtfs_base_dir = stops_path.parent
                    
                    try:
                        self.stops_df = pd.read_csv(stops_path)
                        self.routes_df = pd.read_csv(gtfs_base_dir / 'routes.txt')
                        self.trips_df = pd.read_csv(gtfs_base_dir / 'trips.txt')
                        self.stop_times_df = pd.read_csv(gtfs_base_dir / 'stop_times.txt')
                        
                        try:
                            self.shapes_df = pd.read_csv(gtfs_base_dir / 'shapes.txt')
                        except:
                            self.shapes_df = None
                            
                    except Exception as e:
                        # Try different encodings if default fails
                        for encoding in ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']:
                            try:
                                self.stops_df = pd.read_csv(stops_path, encoding=encoding)
                                break
                            except:
                                continue
                        if self.stops_df is None:
                            raise Exception("Could not read stops.txt with any encoding")
                        
        except Exception as e:
            print(f"Error loading GTFS data: {str(e)}")
            sys.exit(1)
    
    def calculate_stop_metrics(self):
        """Calculate trip and route counts for each stop"""
        trip_counts = (
            self.stop_times_df
            .groupby('stop_id')['trip_id']
            .nunique()
        )
        
        route_counts = (
            self.stop_times_df
            .merge(self.trips_df[['trip_id', 'route_id']], on='trip_id')
            .groupby('stop_id')['route_id']
            .nunique()
        )
        
        return pd.DataFrame({
            'trip_count': trip_counts,
            'route_count': route_counts
        }).fillna(0)

    def create_map(self, output_path=None, stops_only=False, 
                  color_by='trips', cmap='magma', route_cmap='magma', **kwargs):
        """
        Create an interactive map with stops and routes.
        
        Args:
            output_path (str): Path where the HTML map will be saved
            stops_only (bool): If True, only stops will be displayed (no routes)
            color_by (str): 'trips' or 'routes' - metric to use for coloring stops
            cmap (str): Matplotlib colormap name for stops (e.g., 'magma', 'viridis', 'YlOrRd')
            route_cmap (str): Matplotlib colormap name for routes
        
        Example usage:
            creator.create_map(
                "output.html",
                color_by='trips',
                cmap='magma',
                route_cmap='Blues'
            )
        """
        metrics = self.calculate_stop_metrics()
        
        if color_by == 'routes':
            metric_name, legend_name = 'route_count', 'Routes per Stop'
        else:
            metric_name, legend_name = 'trip_count', 'Trips per Stop'
            
        metric_values = metrics[metric_name]
        vmin, vmax = metric_values.min(), metric_values.max()

        # Get colors from matplotlib colormap
        mpl_cmap = plt.get_cmap(cmap)
        colors = [to_hex(mpl_cmap(i)) for i in np.linspace(0, 1, 7)]
        
        colormap = LinearColormap(
            colors=colors,
            vmin=vmin,
            vmax=vmax,
            caption=legend_name,
        )
        
        # Create base map
        m = folium.Map(
            location=[self.stops_df['stop_lat'].mean(), self.stops_df['stop_lon'].mean()], 
            zoom_start=12,
            tiles='cartodbpositron',
            prefer_canvas=True
        )
        
        # Add routes
        if self.shapes_df is not None and not stops_only:
            routes_group = folium.FeatureGroup(name='Routes', show=True)
            route_freqs = self.trips_df['route_id'].value_counts()
            max_freq = route_freqs.max()
            
            # Get route colors from matplotlib
            route_mpl_cmap = plt.get_cmap(route_cmap)
            route_colors = [to_hex(route_mpl_cmap(i)) for i in np.linspace(0, 1, 5)]
            
            for shape_id in self.shapes_df['shape_id'].unique():
                shape_points = (
                    self.shapes_df[self.shapes_df['shape_id'] == shape_id]
                    .sort_values('shape_pt_sequence')
                )
                
                route_id = self.trips_df[
                    self.trips_df['shape_id'] == shape_id
                ]['route_id'].iloc[0]
                freq_ratio = route_freqs.get(route_id, 1) / max_freq
                
                color_idx = int(freq_ratio * (len(route_colors) - 1))
                route_color = route_colors[color_idx]
                
                points = [[row['shape_pt_lat'], row['shape_pt_lon']] 
                         for idx, row in shape_points.iterrows()]
                
                folium.PolyLine(
                    points,
                    weight=2 + freq_ratio * 4,
                    color=route_color,
                    opacity=0.7,
                    smooth_factor=1.5
                ).add_to(routes_group)
            
            routes_group.add_to(m)
        
        # Add stops to the map
        stops_group = folium.FeatureGroup(name='Stops', show=True)
        for idx, stop in self.stops_df.iterrows():
            metric_value = metrics.loc[stop['stop_id'], metric_name] if stop['stop_id'] in metrics.index else 0
            color = colormap(metric_value)
            
            # Calculate size based on metric (with smaller range)
            size_ratio = metric_value / vmax if vmax > 0 else 0
            radius = 4 + size_ratio * 8  # Smaller size range
            
            folium.CircleMarker(
                location=[stop['stop_lat'], stop['stop_lon']],
                radius=radius,
                color=color,
                fill=True,
                fillOpacity=0.7,
                weight=1,  # Thinner border
                popup=folium.Popup(
                    f"""
                    <div style="font-family: Arial, sans-serif;">
                        <strong>{stop['stop_name']}</strong><br>
                        <small>ID: {stop['stop_id']}</small><br>
                        <hr style="margin: 5px 0;">
                        <span style="color: #666;">
                            Trips: {metrics.loc[stop['stop_id'], 'trip_count'] if stop['stop_id'] in metrics.index else 0}<br>
                            Routes: {metrics.loc[stop['stop_id'], 'route_count'] if stop['stop_id'] in metrics.index else 0}
                        </span>
                    </div>
                    """,
                    max_width=200
                )
            ).add_to(stops_group)
        
        stops_group.add_to(m)
        
        # Add colormap to the map with better styling
        colormap.add_to(m)
        
        # Add layer control with expanded view
        folium.LayerControl(collapsed=False).add_to(m)
        
        # Save the map
        if output_path is None:
            output_path = self.gtfs_path.replace(".zip", "_map.html")
        m.save(output_path)

        # print(f"Map created successfully at {output_path}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Create an interactive map from GTFS data')
    parser.add_argument('gtfs_path', help='Path to the GTFS zip file')
    parser.add_argument('--output', default='transit_map.html', help='Output HTML file path')
    parser.add_argument('--stops-only', action='store_true', help='Show only stops, no routes')
    parser.add_argument('--color-by', choices=['trips', 'routes'], default='trips',
                      help='Metric to use for coloring stops')
    parser.add_argument('--cmap', default='magma',
                      help='Matplotlib colormap name for stops')
    parser.add_argument('--route-cmap', default='magma',
                      help='Matplotlib colormap name for routes')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.gtfs_path):
        print(f"Error: Input file '{args.gtfs_path}' does not exist")
        sys.exit(1)
    
    map_creator = GTFSMapCreator(args.gtfs_path)
    map_creator.load_gtfs_data()
    map_creator.create_map(**vars(args))

if __name__ == "__main__":
    main() 