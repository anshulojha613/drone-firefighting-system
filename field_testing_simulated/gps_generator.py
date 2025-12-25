#!/usr/bin/env python3
"""
GPS Telemetry Generator
Generates realistic GPS data with noise and wind effects
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import yaml
import math


class GPSGenerator:
    def __init__(self, config_file: str = "simulation_config.yaml"):
        """Initialize GPS generator with config"""
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.gps_config = self.config['gps']
        self.drone_config = self.config['drone']
        self.sim_config = self.config['simulation']
        
        # Set random seed for reproducibility
        if self.sim_config.get('random_seed'):
            np.random.seed(self.sim_config['random_seed'])
    
    def add_gps_noise(self, lat: float, lon: float, alt: float) -> Tuple[float, float, float]:
        """Add realistic GPS noise to coordinates"""
        if not self.sim_config['add_gps_drift']:
            return lat, lon, alt
        
        # Horizontal noise (Gaussian distribution)
        h_noise = self.gps_config['noise']['horizontal_m']
        
        # Convert meters to degrees (approximate)
        lat_noise = np.random.normal(0, h_noise / 111320)  # 1 degree lat ≈ 111.32 km
        lon_noise = np.random.normal(0, h_noise / (111320 * math.cos(math.radians(lat))))
        
        # Vertical noise
        v_noise = self.gps_config['noise']['vertical_m']
        alt_noise = np.random.normal(0, v_noise)
        
        return lat + lat_noise, lon + lon_noise, alt + alt_noise
    
    def add_wind_effect(self, lat: float, lon: float, heading: float, 
                       elapsed_time: float) -> Tuple[float, float, float]:
        """Add wind drift effect to position"""
        if not self.sim_config['add_wind_effects']:
            return lat, lon, heading
        
        wind_config = self.drone_config['wind']
        
        # Random wind speed within range
        wind_speed_ms = np.random.uniform(*wind_config['speed_ms'])
        
        # Random wind direction
        wind_direction = np.random.uniform(*wind_config['direction_deg'])
        
        # Calculate wind drift (simplified)
        # Drift increases with time and wind speed
        drift_factor = 0.1  # Drone compensates for most wind
        drift_distance = wind_speed_ms * drift_factor
        
        # Convert drift to lat/lon offset
        drift_lat = drift_distance * math.cos(math.radians(wind_direction)) / 111320
        drift_lon = drift_distance * math.sin(math.radians(wind_direction)) / (111320 * math.cos(math.radians(lat)))
        
        # Heading variation due to wind
        heading_variation = np.random.normal(0, self.gps_config['noise']['heading_deg'])
        
        return lat + drift_lat, lon + drift_lon, (heading + heading_variation) % 360
    
    def interpolate_path(self, start: Dict, end: Dict, num_points: int) -> List[Dict]:
        """Interpolate GPS points between two waypoints"""
        points = []
        
        for i in range(num_points):
            t = i / (num_points - 1) if num_points > 1 else 0
            
            # Linear interpolation
            lat = start['latitude'] + t * (end['latitude'] - start['latitude'])
            lon = start['longitude'] + t * (end['longitude'] - start['longitude'])
            alt = start['altitude_m'] + t * (end['altitude_m'] - start['altitude_m'])
            
            # Calculate heading
            if i < num_points - 1:
                next_t = (i + 1) / (num_points - 1)
                next_lat = start['latitude'] + next_t * (end['latitude'] - start['latitude'])
                next_lon = start['longitude'] + next_t * (end['longitude'] - start['longitude'])
                heading = self.calculate_bearing(lat, lon, next_lat, next_lon)
            else:
                heading = points[-1]['heading'] if points else 0
            
            points.append({
                'latitude': lat,
                'longitude': lon,
                'altitude': alt,
                'heading': heading
            })
        
        return points
    
    def calculate_bearing(self, lat1: float, lon1: float, 
                         lat2: float, lon2: float) -> float:
        """Calculate bearing between two points"""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlon = math.radians(lon2 - lon1)
        
        y = math.sin(dlon) * math.cos(lat2_rad)
        x = (math.cos(lat1_rad) * math.sin(lat2_rad) -
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon))
        
        bearing = math.degrees(math.atan2(y, x))
        return (bearing + 360) % 360
    
    def calculate_distance(self, lat1: float, lon1: float,
                          lat2: float, lon2: float) -> float:
        """Calculate distance between two points in meters"""
        R = 6371000  # Earth radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def generate_telemetry(self, waypoints: List[Dict], 
                          start_time: datetime) -> pd.DataFrame:
        """Generate complete GPS telemetry data"""
        telemetry = []
        current_time = start_time
        update_interval = 1.0 / self.gps_config['update_rate_hz']
        
        print(f"\n[GPS]  Generating GPS telemetry...")
        print(f"   Update rate: {self.gps_config['update_rate_hz']} Hz")
        print(f"   Waypoints: {len(waypoints)}")
        
        # Process each waypoint segment
        for i in range(len(waypoints) - 1):
            wp_start = waypoints[i]
            wp_end = waypoints[i + 1]
            
            # Calculate segment distance and time
            distance = self.calculate_distance(
                wp_start['latitude'], wp_start['longitude'],
                wp_end['latitude'], wp_end['longitude']
            )
            
            # Determine speed based on waypoint type
            if wp_start['type'] == 'takeoff':
                speed = self.drone_config['ascent_rate_ms']
                altitude_change = wp_end['altitude_m'] - wp_start['altitude_m']
                segment_time = abs(altitude_change / speed)
            elif wp_end['type'] == 'land':
                speed = self.drone_config['descent_rate_ms']
                altitude_change = wp_start['altitude_m'] - wp_end['altitude_m']
                segment_time = abs(altitude_change / speed)
            else:
                speed = self.drone_config['cruise_speed_ms']
                segment_time = distance / speed if speed > 0 else 1
            
            # Number of GPS readings for this segment
            num_readings = max(int(segment_time / update_interval), 2)
            
            # Interpolate path
            path_points = self.interpolate_path(wp_start, wp_end, num_readings)
            
            # Generate telemetry for each point
            for j, point in enumerate(path_points):
                # Add noise and wind effects
                lat, lon, alt = self.add_gps_noise(
                    point['latitude'],
                    point['longitude'],
                    point['altitude']
                )
                
                elapsed = (current_time - start_time).total_seconds()
                lat, lon, heading = self.add_wind_effect(
                    lat, lon, point['heading'], elapsed
                )
                
                # Random satellite count
                satellites = np.random.randint(*self.gps_config['satellites'])
                
                # GPS dropout simulation
                if np.random.random() < self.sim_config['gps_dropout_probability']:
                    # Skip this reading (GPS dropout)
                    current_time += timedelta(seconds=update_interval)
                    continue
                
                telemetry.append({
                    'timestamp': current_time.isoformat(),
                    'latitude': lat,
                    'longitude': lon,
                    'altitude': alt,
                    'heading': heading % 360,
                    'satellites': satellites,
                    'fix_type': self.gps_config['fix_type'],
                    'mode': 'simulated'
                })
                
                current_time += timedelta(seconds=update_interval)
        
        # Convert to DataFrame
        df = pd.DataFrame(telemetry)
        
        print(f"   [OK] Generated {len(df)} GPS readings")
        print(f"   Duration: {(current_time - start_time).total_seconds():.1f}s")
        
        return df
    
    def save_telemetry(self, df: pd.DataFrame, output_file: str):
        """Save GPS telemetry to CSV file"""
        df.to_csv(output_file, index=False)
        print(f"   [OK] Saved to: {output_file}")


def main():
    """Test GPS generator"""
    from flight_path_calculator import FlightPathCalculator
    
    # Generate waypoints
    calculator = FlightPathCalculator()
    waypoints = calculator.generate_waypoints()
    
    # Generate GPS telemetry
    generator = GPSGenerator()
    
    # Parse start time from config
    with open('simulation_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    start_time_str = config['mission']['start_time']
    start_time = datetime.strptime(start_time_str, '%Y%m%d_%H%M%S')
    
    # Generate telemetry
    telemetry = generator.generate_telemetry(waypoints, start_time)
    
    # Display sample
    print("\n[STATS] Sample GPS data:")
    print(telemetry.head(10))
    
    print(f"\n Statistics:")
    print(f"   Total readings: {len(telemetry)}")
    print(f"   Lat range: {telemetry['latitude'].min():.7f} to {telemetry['latitude'].max():.7f}")
    print(f"   Lon range: {telemetry['longitude'].min():.7f} to {telemetry['longitude'].max():.7f}")
    print(f"   Alt range: {telemetry['altitude'].min():.1f}m to {telemetry['altitude'].max():.1f}m")


if __name__ == '__main__':
    main()
