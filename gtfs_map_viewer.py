import pandas as pd
import folium
from pathlib import Path
import zipfile
import tempfile
import os
import sys

class GTFSMapCreator:
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
            print(f"Checking zip file: {self.gtfs_path}")
            with zipfile.ZipFile(self.gtfs_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                print(f"Files in zip: {file_list}")
                
                # Check for stops.txt in any directory
                stops_file = None
                for f in file_list:
                    if f.lower().endswith('stops.txt'):
                        stops_file = f
                        print(f"Found stops file at: {stops_file}")
                        break
                
                if not stops_file:
                    print("No stops.txt file found in any directory")
                    return False
                return True
        except zipfile.BadZipFile:
            print(f"Error: {self.gtfs_path} is not a valid zip file")
            return False
        except Exception as e:
            print(f"Error validating GTFS file: {str(e)}")
            return False

    def load_gtfs_data(self):
        """Load required GTFS files into pandas dataframes"""
        if not self.validate_gtfs_file():
            sys.exit(1)

        try:
            with zipfile.ZipFile(self.gtfs_path, 'r') as zip_ref:
                print(f"Opening zip file: {self.gtfs_path}")
                # Create a temporary directory to extract files
                with tempfile.TemporaryDirectory() as tmpdir:
                    print(f"Created temp directory: {tmpdir}")
                    
                    # Extract all files first
                    zip_ref.extractall(tmpdir)
                    print(f"Extracted files to: {tmpdir}")
                    
                    # Find stops.txt recursively
                    stops_path = None
                    for root, dirs, files in os.walk(tmpdir):
                        for file in files:
                            if file.lower() == 'stops.txt':
                                stops_path = os.path.join(root, file)
                                break
                        if stops_path:
                            break
                    
                    if not stops_path:
                        raise Exception(f"stops.txt not found in {tmpdir}")
                    
                    print(f"Reading stops.txt from: {stops_path}")
                    try:
                        self.stops_df = pd.read_csv(stops_path)
                        print(f"Successfully loaded stops.txt with {len(self.stops_df)} rows")
                    except Exception as e:
                        print(f"Error reading stops.txt: {str(e)}")
                        # Try different encodings
                        for encoding in ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']:
                            try:
                                print(f"Trying encoding: {encoding}")
                                self.stops_df = pd.read_csv(stops_path, encoding=encoding)
                                print(f"Successfully loaded stops.txt with encoding {encoding}")
                                break
                            except Exception as e:
                                print(f"Failed with encoding {encoding}: {str(e)}")
                        if self.stops_df is None:
                            raise Exception("Could not read stops.txt with any encoding")

                    # Get the base directory where stops.txt was found
                    gtfs_base_dir = os.path.dirname(stops_path)
                    
                    # Try to load optional files from the same directory
                    try:
                        self.routes_df = pd.read_csv(os.path.join(gtfs_base_dir, 'routes.txt'))
                        self.trips_df = pd.read_csv(os.path.join(gtfs_base_dir, 'trips.txt'))
                        self.stop_times_df = pd.read_csv(os.path.join(gtfs_base_dir, 'stop_times.txt'))
                    except Exception as e:
                        print(f"Warning: Could not load some optional files: {str(e)}")
                        pass

                    # Shapes are optional in GTFS
                    try:
                        self.shapes_df = pd.read_csv(os.path.join(gtfs_base_dir, 'shapes.txt'))
                    except:
                        self.shapes_df = None
                        print("Note: shapes.txt not found or could not be loaded")
                        
        except Exception as e:
            print(f"Error loading GTFS data: {str(e)}")
            sys.exit(1)
    
    def create_map(self, output_path='transit_map.html', stops_only=False):
        """Create an interactive map with stops and routes
        
        Args:
            output_path (str): Path where the HTML map will be saved
            stops_only (bool): If True, only stops will be displayed (no routes)
        """
        # Calculate the center of the map
        center_lat = self.stops_df['stop_lat'].mean()
        center_lon = self.stops_df['stop_lon'].mean()
        
        # Create a base map
        m = folium.Map(location=[center_lat, center_lon], 
                      zoom_start=12,
                      tiles='cartodbpositron')
        
        # Add stops to the map
        stops_group = folium.FeatureGroup(name='Stops')
        for idx, stop in self.stops_df.iterrows():
            folium.CircleMarker(
                location=[stop['stop_lat'], stop['stop_lon']],
                radius=5,
                color='red',
                fill=True,
                popup=f"Stop: {stop['stop_name']}<br>ID: {stop['stop_id']}",
                weight=2
            ).add_to(stops_group)
        
        stops_group.add_to(m)
        
        # Add routes if shapes are available and stops_only is False
        if self.shapes_df is not None and not stops_only:
            routes_group = folium.FeatureGroup(name='Routes')
            
            # Group shapes by shape_id
            for shape_id in self.shapes_df['shape_id'].unique():
                shape_points = self.shapes_df[self.shapes_df['shape_id'] == shape_id].sort_values('shape_pt_sequence')
                
                # Create a line for each shape
                points = [[row['shape_pt_lat'], row['shape_pt_lon']] 
                         for idx, row in shape_points.iterrows()]
                
                folium.PolyLine(
                    points,
                    weight=2,
                    color='blue',
                    opacity=0.5
                ).add_to(routes_group)
            
            routes_group.add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Save the map
        m.save(output_path)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Create an interactive map from GTFS data')
    parser.add_argument('gtfs_path', help='Path to the GTFS zip file')
    parser.add_argument('--output', default='transit_map.html', help='Output HTML file path')
    parser.add_argument('--stops-only', action='store_true', 
                      help='Show only stops, no routes')
    
    args = parser.parse_args()
    
    # Verify the input file exists
    if not os.path.exists(args.gtfs_path):
        print(f"Error: Input file '{args.gtfs_path}' does not exist")
        sys.exit(1)
    
    # Create map
    map_creator = GTFSMapCreator(args.gtfs_path)
    map_creator.load_gtfs_data()
    map_creator.create_map(args.output, stops_only=args.stops_only)
    print(f"Map created successfully at {args.output}")

if __name__ == "__main__":
    main() 