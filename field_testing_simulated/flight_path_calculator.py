#!/usr/bin/env python3
"""
Flight Path Calculator
Calculates best flight path for area coverage with thermal camera
"""

import numpy as np
import yaml
from pathlib import Path
from typing import List, Dict, Tuple
import math


class FlightPathCalculator:
    def __init__(self, config_file: str = "simulation_config.yaml"):
        """Initialize flight path calculator with config"""
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.flight_area = self.config['flight_area']
        self.thermal = self.config['thermal_camera']
        self.drone = self.config['drone']
        
    def calculate_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """
        Calculate distance between two GPS coordinates using Haversine formula
        """
        R = 6371000  # Earth radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def calculate_bearing(self, lat1: float, lon1: float,
                         lat2: float, lon2: float) -> float:
        """
        Calculate bearing from point 1 to point 2
        """
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlon = math.radians(lon2 - lon1)
        
        y = math.sin(dlon) * math.cos(lat2_rad)
        x = (math.cos(lat1_rad) * math.sin(lat2_rad) -
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon))
        
        bearing = math.degrees(math.atan2(y, x))
        return (bearing + 360) % 360
    
    def offset_coordinate(self, lat: float, lon: float,
                         distance_m: float, bearing_deg: float) -> Tuple[float, float]:
        """
        Calculate new coordinate given distance and bearing
        """
        R = 6371000  # Earth radius in meters
        
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        bearing_rad = math.radians(bearing_deg)
        
        new_lat_rad = math.asin(
            math.sin(lat_rad) * math.cos(distance_m / R) +
            math.cos(lat_rad) * math.sin(distance_m / R) * math.cos(bearing_rad)
        )
        
        new_lon_rad = lon_rad + math.atan2(
            math.sin(bearing_rad) * math.sin(distance_m / R) * math.cos(lat_rad),
            math.cos(distance_m / R) - math.sin(lat_rad) * math.sin(new_lat_rad)
        )
        
        return math.degrees(new_lat_rad), math.degrees(new_lon_rad)
    
    def calculate_area_dimensions(self) -> Dict:
        """Calculate actual area dimensions"""
        corner_a = self.flight_area['corner_a']
        corner_b = self.flight_area['corner_b']
        corner_c = self.flight_area['corner_c']
        corner_d = self.flight_area['corner_d']
        
        # Width: A to B (East to West)
        width_m = self.calculate_distance(
            corner_a['latitude'], corner_a['longitude'],
            corner_b['latitude'], corner_b['longitude']
        )
        
        # Height: B to C (North to South)
        height_m = self.calculate_distance(
            corner_b['latitude'], corner_b['longitude'],
            corner_c['latitude'], corner_c['longitude']
        )
        
        return {
            'width_m': width_m,
            'height_m': height_m,
            'width_ft': width_m * 3.28084,
            'height_ft': height_m * 3.28084,
            'area_m2': width_m * height_m,
            'area_acres': (width_m * height_m) / 4046.86
        }
    
    def calculate_thermal_coverage(self) -> Dict:
        """Calcrmal camera ground coverage at cruise altitude"""
        altitude_m = self.drone['cruise_altitude_m']
        h_fov = self.thermal['field_of_view']['horizontal_deg']
        v_fov = self.thermal['field_of_view']['vertical_deg']
        
        # Ground coverage = 2 * altitude * tan(FOV/2)
        width_m = 2 * altitude_m * math.tan(math.radians(h_fov / 2))
        height_m = 2 * altitude_m * math.tan(math.radians(v_fov / 2))
        
        return {
            'width_m': width_m,
            'height_m': height_m,
            'width_ft': width_m * 3.28084,
            'height_ft': height_m * 3.28084
        }
    
    def calculate_effective_coverage(self, overlap_percent: float = 30) -> Dict:
        """Calculate effective coverage accounting for overlap"""
        coverage = self.calculate_thermal_coverage()
        
        effective_width = coverage['width_m'] * (1 - overlap_percent / 100)
        effective_height = coverage['height_m'] * (1 - overlap_percent / 100)
        
        return {
            'width_m': effective_width,
            'height_m': effective_height,
            'overlap_percent': overlap_percent
        }
    
    def calculate_flight_params(self) -> Dict:
        """Calculate complete flight params"""
        area = self.calculate_area_dimensions()
        coverage = self.calculate_thermal_coverage()
        effective = self.calculate_effective_coverage(
            self.thermal['overlap']['recommended_percent']
        )
        
        # Number of passes required
        passes = math.ceil(area['height_m'] / effective['height_m'])
        
        # Total distance
        straight_distance = passes * area['width_m']
        turn_distance = (passes - 1) * effective['height_m']
        total_distance = straight_distance + turn_distance
        
        # Time calculations
        cruise_speed = self.drone['cruise_speed_ms']
        ascent_rate = self.drone['ascent_rate_ms']
        descent_rate = self.drone['descent_rate_ms']
        altitude = self.drone['cruise_altitude_m']
        
        cruise_time = total_distance / cruise_speed
        ascent_time = altitude / ascent_rate
        descent_time = altitude / descent_rate
        hover_time = 20  # Pre-flight and post-landing
        
        total_time = cruise_time + ascent_time + descent_time + hover_time
        
        # Battery usage
        max_flight_time = self.drone['max_flight_time_min'] * 60
        battery_usage = (total_time / max_flight_time) * 100
        
        return {
            'area': area,
            'thermal_coverage': coverage,
            'effective_coverage': effective,
            'passes_required': passes,
            'distances': {
                'straight_m': straight_distance,
                'turns_m': turn_distance,
                'total_m': total_distance,
                'total_km': total_distance / 1000,
                'total_miles': total_distance / 1609.34
            },
            'times': {
                'cruise_sec': cruise_time,
                'ascent_sec': ascent_time,
                'descent_sec': descent_time,
                'hover_sec': hover_time,
                'total_sec': total_time,
                'total_min': total_time / 60
            },
            'battery': {
                'usage_percent': battery_usage,
                'remaining_min': (max_flight_time - total_time) / 60
            }
        }
    
    def generate_waypoints(self) -> List[Dict]:
        """Generate waypoint list for serpentine flight pattern"""
        corner_a = self.flight_area['corner_a']
        corner_b = self.flight_area['corner_b']
        corner_d = self.flight_area['corner_d']
        
        params = self.calculate_flight_params()
        passes = params['passes_required']
        effective_height = params['effective_coverage']['height_m']
        
        waypoints = []
        
        # Waypoint 0: Start at A (ground level)
        waypoints.append({
            'id': 0,
            'type': 'takeoff',
            'latitude': corner_a['latitude'],
            'longitude': corner_a['longitude'],
            'altitude_m': 0,
            'action': 'takeoff'
        })
        
        # Calculate bearing from A to B (East to West)
        bearing_ew = self.calculate_bearing(
            corner_a['latitude'], corner_a['longitude'],
            corner_b['latitude'], corner_b['longitude']
        )
        
        # Calculate bearing for North to South movement
        bearing_ns = self.calculate_bearing(
            corner_a['latitude'], corner_a['longitude'],
            corner_d['latitude'], corner_d['longitude']
        )
        
        current_lat = corner_a['latitude']
        current_lon = corner_a['longitude']
        
        # Generate serpentine pattern waypoints
        for pass_num in range(passes):
            # Move south for each pass
            if pass_num > 0:
                current_lat, current_lon = self.offset_coordinate(
                    current_lat, current_lon,
                    effective_height, bearing_ns
                )
            
            # Waypoint at start of pass
            waypoints.append({
                'id': len(waypoints),
                'type': 'scan',
                'latitude': current_lat,
                'longitude': current_lon,
                'altitude_m': self.drone['cruise_altitude_m'],
                'action': 'scan',
                'pass_number': pass_num + 1
            })
            
            # Waypoint at end of pass (East to West)
            if pass_num % 2 == 0:
                # Even passes: A to B direction
                end_lat, end_lon = self.offset_coordinate(
                    current_lat, current_lon,
                    params['area']['width_m'], bearing_ew
                )
            else:
                # Odd passes: B to A direction (reverse)
                end_lat, end_lon = self.offset_coordinate(
                    current_lat, current_lon,
                    params['area']['width_m'], (bearing_ew + 180) % 360
                )
            
            waypoints.append({
                'id': len(waypoints),
                'type': 'scan',
                'latitude': end_lat,
                'longitude': end_lon,
                'altitude_m': self.drone['cruise_altitude_m'],
                'action': 'scan',
                'pass_number': pass_num + 1
            })
            
            current_lat = end_lat
            current_lon = end_lon
        
        # Final waypoint: Return to A
        waypoints.append({
            'id': len(waypoints),
            'type': 'rtl',
            'latitude': corner_a['latitude'],
            'longitude': corner_a['longitude'],
            'altitude_m': self.drone['cruise_altitude_m'],
            'action': 'return_to_launch'
        })
        
        # Landing waypoint
        waypoints.append({
            'id': len(waypoints),
            'type': 'land',
            'latitude': corner_a['latitude'],
            'longitude': corner_a['longitude'],
            'altitude_m': 0,
            'action': 'land'
        })
        
        return waypoints
    
    def print_summary(self):
        """Print flight params summary"""
        params = self.calculate_flight_params()
        
        print("\n" + "="*70)
        print("FLIGHT PATH CALCULATION SUMMARY")
        print("="*70)
        
        print("\n AREA DIMENSIONS:")
        print(f"  Width:  {params['area']['width_m']:.1f}m ({params['area']['width_ft']:.1f}ft)")
        print(f"  Height: {params['area']['height_m']:.1f}m ({params['area']['height_ft']:.1f}ft)")
        print(f"  Area:   {params['area']['area_m2']:.1f}m² ({params['area']['area_acres']:.2f} acres)")
        
        print("\n THERMAL CAMERA COVERAGE:")
        print(f"  At {self.drone['cruise_altitude_ft']}ft altitude:")
        print(f"  Width:  {params['thermal_coverage']['width_m']:.1f}m ({params['thermal_coverage']['width_ft']:.1f}ft)")
        print(f"  Height: {params['thermal_coverage']['height_m']:.1f}m ({params['thermal_coverage']['height_ft']:.1f}ft)")
        
        print("\n  EFFECTIVE COVERAGE (with overlap):")
        print(f"  Overlap: {params['effective_coverage']['overlap_percent']}%")
        print(f"  Width:  {params['effective_coverage']['width_m']:.1f}m")
        print(f"  Height: {params['effective_coverage']['height_m']:.1f}m")
        
        print("\n FLIGHT PARAMETERS:")
        print(f"  Passes required: {params['passes_required']}")
        print(f"  Cruise speed: {self.drone['cruise_speed_ms']}m/s")
        print(f"  Total distance: {params['distances']['total_m']:.1f}m ({params['distances']['total_miles']:.2f} miles)")
        
        print("\n[TIME]  TIME ESTIMATES:")
        print(f"  Ascent:  {params['times']['ascent_sec']:.1f}s")
        print(f"  Cruise:  {params['times']['cruise_sec']:.1f}s ({params['times']['cruise_sec']/60:.1f}min)")
        print(f"  Descent: {params['times']['descent_sec']:.1f}s")
        print(f"  Hover:   {params['times']['hover_sec']:.1f}s")
        print(f"  TOTAL:   {params['times']['total_min']:.1f} minutes")
        
        print("\n[BATTERY] BATTERY USAGE:")
        print(f"  Estimated usage: {params['battery']['usage_percent']:.1f}%")
        print(f"  Remaining time:  {params['battery']['remaining_min']:.1f} minutes")
        print(f"  Safety margin:   {'[OK] SAFE' if params['battery']['usage_percent'] < 60 else ' WARNING'}")
        
        print("\n" + "="*70 + "\n")


def main():
    """Main function for testing"""
    calculator = FlightPathCalculator()
    
    # Print summary
    calculator.print_summary()
    
    # Generate waypoints
    waypoints = calculator.generate_waypoints()
    
    print(f"[LOC] Generated {len(waypoints)} waypoints")
    print("\nFirst 5 waypoints:")
    for wp in waypoints[:5]:
        print(f"  WP{wp['id']}: {wp['type']} at ({wp['latitude']:.7f}, {wp['longitude']:.7f}) "
              f"alt={wp['altitude_m']:.1f}m")
    
    print(f"\nLast 3 waypoints:")
    for wp in waypoints[-3:]:
        print(f"  WP{wp['id']}: {wp['type']} at ({wp['latitude']:.7f}, {wp['longitude']:.7f}) "
              f"alt={wp['altitude_m']:.1f}m")


if __name__ == '__main__':
    main()
