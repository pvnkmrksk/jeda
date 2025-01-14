import partridge as ptg
import pandas as pd
import re
from typing import List, Set, Dict, Union
from pathlib import Path
from datetime import datetime
import argparse

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
    
    def subset_by_min_trips(self, min_trips: int) -> Set[str]:
        """
        Get trips from routes that have at least min_trips trips in the static schedule
        """
        route_trip_counts = (
            self.feed.trips
            .groupby('route_id')
            .size()
        )
        qualifying_routes = route_trip_counts[route_trip_counts >= min_trips].index
        
        return set(
            self.feed.trips[
                self.feed.trips['route_id'].isin(qualifying_routes)
            ]['trip_id']
        )

    def create_subset(self, 
                     output_path: str,
                     stop_ids: List[str] = None,
                     route_patterns: List[str] = None,
                     min_trips: int = None) -> 'GTFSAnalyzer':
        """
        Create a GTFS subset by chaining multiple filters.
        Returns a new GTFSAnalyzer instance with the subset feed.
        
        Parameters:
        -----------
        output_path : str
            Path where the subset GTFS will be saved
        stop_ids : List[str], optional
            List of stop IDs to include. If provided without routes, includes all routes serving these stops.
        route_patterns : List[str], optional
            List of route patterns (supports wildcards like "138*"). If provided without stops, 
            includes only stops served by these routes.
        min_trips : int, optional
            Minimum number of trips a route must have to be included
        """
        qualifying_trips = set()
        
        # First handle route patterns if specified
        if route_patterns and len(route_patterns) > 0:
            regex_pattern = '|'.join([p.replace('*', '.*') for p in route_patterns])
            route_trips = set(
                self.feed.trips[
                    self.feed.trips['route_id'].isin(
                        self.feed.routes[
                            self.feed.routes['route_short_name'].str.match(
                                regex_pattern, na=False
                            )
                        ]['route_id']
                    )
                ]['trip_id']
            )
            qualifying_trips = route_trips
        
        # Then handle stops if specified
        if stop_ids and len(stop_ids) > 0:
            stop_trips = set(
                self.feed.stop_times[
                    self.feed.stop_times['stop_id'].isin(stop_ids)
                ]['trip_id']
            )
            # If routes were specified, intersect with stop_trips
            # If no routes were specified, use all trips through these stops
            qualifying_trips = (
                qualifying_trips & stop_trips 
                if qualifying_trips 
                else stop_trips
            )
        
        # If neither stops nor routes specified, use all trips
        if not qualifying_trips:
            qualifying_trips = set(self.feed.trips['trip_id'])
        
        # Apply minimum trips filter if specified
        if min_trips:
            min_trip_ids = self.subset_by_min_trips(min_trips)
            qualifying_trips &= min_trip_ids
            
        # Create view for partridge
        view = {'trips.txt': {'trip_id': list(qualifying_trips)}}
        
        # Extract subset
        ptg.extract_feed(self.feed_path, output_path, view)
        return GTFSAnalyzer(output_path)