import partridge as ptg
import pandas as pd
import re
from typing import List, Set, Dict, Union
from pathlib import Path

class GTFSAnalyzer:
    """
    A class to analyze GTFS feeds with various metrics and subsetting capabilities
    """
    
    def __init__(self, feed_path: Union[str, Path]):
        """Initialize with a GTFS feed path"""
        self.feed_path = str(feed_path)
        self.feed = ptg.load_feed(self.feed_path)
        
    def analyze_stop_metrics(self, output_dir: str = "analysis") -> Dict[str, pd.DataFrame]:
        """
        Analyze stops based on different metrics:
        1. Stops with most trips
        2. Stops with most unique routes
        3. Routes with most trips
        
        Returns dictionary containing all analysis dataframes
        """
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        # 1. Stops with most trips
        stop_trip_counts = (
            self.feed.stop_times
            .groupby('stop_id')['trip_id']
            .nunique()
            .reset_index(name='trip_count')
            .merge(self.feed.stops[['stop_id', 'stop_name']], on='stop_id')
            .sort_values('trip_count', ascending=False)
        )
        results['stops_by_trips'] = stop_trip_counts
        
        # 2. Stops with most unique routes
        stop_route_counts = (
            self.feed.stop_times
            .merge(self.feed.trips[['trip_id', 'route_id']], on='trip_id')
            .groupby('stop_id')['route_id']
            .nunique()
            .reset_index(name='route_count')
            .merge(self.feed.stops[['stop_id', 'stop_name']], on='stop_id')
            .sort_values('route_count', ascending=False)
        )
        results['stops_by_routes'] = stop_route_counts
        
        # 3. Routes with most trips
        route_trip_counts = (
            self.feed.trips
            .groupby('route_id')
            .size()
            .reset_index(name='trip_count')
            .merge(self.feed.routes[['route_id', 'route_short_name', 'route_long_name']], on='route_id')
            .sort_values('trip_count', ascending=False)
        )
        results['routes_by_trips'] = route_trip_counts
        
        # Save results to CSV
        for name, df in results.items():
            df.to_csv(f"{output_dir}/{name}.csv", index=False)
            
        return results
    
    def subset_by_stops(self, stop_ids: List[str], output_path: str) :
        """
        Create a GTFS subset containing only trips that serve specified stops
        """
        # Get all trips that serve these stops
        trips_through_stops = (
            self.feed.stop_times[self.feed.stop_times['stop_id'].isin(stop_ids)]
            ['trip_id']
            .unique()
        )
        
        # Create view for partridge
        view = {'trips.txt': {'trip_id': trips_through_stops}}
        
        # Extract subset
        ptg.extract_feed(self.feed_path, output_path, view)
        return ptg.load_feed(output_path)
    
    def subset_by_route_pattern(self, patterns: List[str], output_path: str):
        """
        Create a GTFS subset containing only routes matching any of the given patterns.
        Patterns can be simple wildcards like "138*" or "KBS*".
        """
        # Convert wildcard patterns to a single regex pattern
        regex_pattern = '|'.join([pattern.replace('*', '.*') for pattern in patterns])
        
        # Find matching route_ids
        matching_routes = (
            self.feed.routes[
                self.feed.routes['route_short_name'].str.match(regex_pattern, na=False)
            ]['route_id']
            .unique()
        )
        
        # Get all trips for matching routes
        matching_trips = (
            self.feed.trips[
                self.feed.trips['route_id'].isin(matching_routes)
            ]['trip_id']
            .unique()
        )
        
        # Create view for partridge
        view = {'trips.txt': {'trip_id': matching_trips}}
        
        # Extract subset
        ptg.extract_feed(self.feed_path, output_path, view)
        return ptg.load_feed(output_path) 