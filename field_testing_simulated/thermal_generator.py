#!/usr/bin/env python3
"""
Thermal Data Generator
Generates realistic thermal camera data with hotspots
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple
import yaml
import math


class ThermalGenerator:
    def __init__(self, config_file: str = "simulation_config.yaml"):
        """Initrmal generator with config"""
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.thermal_config = self.config['thermal_camera']
        self.hotspot_config = self.config['hotspots']
        self.sim_config = self.config['simulation']
        
        # Thermal camera resolution
        self.width = self.thermal_config['resolution']['width']
        self.height = self.thermal_config['resolution']['height']
        
        # Set random seed
        if self.sim_config.get('random_seed'):
            np.random.seed(self.sim_config['random_seed'])
    
    def calculate_distance(self, lat1: float, lon1: float,
                          lat2: float, lon2: float) -> float:
        """Calculate distance between two points in meters"""
        R = 6371000
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def gps_to_pixel(self, drone_lat: float, drone_lon: float, 
                     target_lat: float, target_lon: float,
                     drone_heading: float) -> Tuple[int, int]:
        """
        Convert GPS coordinates to thermal camera pixel coordinates
        """
        # Calculate relative position
        dlat = target_lat - drone_lat
        dlon = target_lon - drone_lon
        
        # Convert to meters (approximate)
        dx = dlon * 111320 * math.cos(math.radians(drone_lat))
        dy = dlat * 111320
        
        # Rotate based on drone heading
        heading_rad = math.radians(drone_heading)
        dx_rot = dx * math.cos(heading_rad) + dy * math.sin(heading_rad)
        dy_rot = -dx * math.sin(heading_rad) + dy * math.cos(heading_rad)
        
        # Get camera coverage at altitude
        altitude = self.config['drone']['cruise_altitude_m']
        coverage_width = self.thermal_config['coverage_at_altitude']['width_m']
        coverage_height = self.thermal_config['coverage_at_altitude']['height_m']
        
        # Convert to pixel coordinates
        # Center of frame is directly below drone
        pixel_x = (dx_rot / coverage_width + 0.5) * self.width
        pixel_y = (dy_rot / coverage_height + 0.5) * self.height
        
        # Check if in view
        if 0 <= pixel_x < self.width and 0 <= pixel_y < self.height:
            return int(pixel_y), int(pixel_x)
        else:
            return -1, -1
    
    def create_base_frame(self, ambient_temp: float) -> np.ndarray:
        """Create base thermal frame with ambient temperature and noise"""
        # Base temperature
        frame = np.full((self.height, self.width), ambient_temp, dtype=np.float32)
        
        # Add spatial temperature variation (natural gradient)
        y_grad = np.linspace(-0.5, 0.5, self.height)[:, np.newaxis]
        x_grad = np.linspace(-0.5, 0.5, self.width)[np.newaxis, :]
        frame += y_grad * 0.3 + x_grad * 0.2
        
        # Add thermal noise
        if self.sim_config['add_thermal_noise']:
            noise = np.random.normal(0, self.thermal_config['noise_c'], 
                                    (self.height, self.width))
            frame += noise
        
        # Round to 2 decimal places to match real MLX90640 sensor precision
        frame = np.round(frame, 2)
        
        return frame
    
    def add_realistic_fire_hotspot(self, frame: np.ndarray, center_row: int, center_col: int,
                                  size: List[int], temperature: float, intensity: float) -> np.ndarray:
        """
        Add a realistic fire hotspot with spread, gradients, and motion blur
        to match actual thermal camera captures of fires
        """
        width_px, height_px = size
        
        # Expand area for realistic spread (reduced to 1/3 of previous size)
        spread_factor = 0.8  # Fire spreads 0.8x of core size (smaller, more realistic)
        spread_width = int(width_px * spread_factor)
        spread_height = int(height_px * spread_factor)
        
        # Create multiple heat cores (fires have multiple hot spots)
        num_cores = np.random.randint(2, 5)  # 2-4 hot cores per fire
        
        for _ in range(num_cores):
            # Offset cores slightly from center for irregular pattern
            core_offset_r = np.random.randint(-height_px, height_px + 1)
            core_offset_c = np.random.randint(-width_px, width_px + 1)
            core_r = center_row + core_offset_r
            core_c = center_col + core_offset_c
            
            # Random core temperature variation
            core_temp = temperature * np.random.uniform(0.7, 1.0)
            
            # Apply heat with irregular falloff
            for r in range(max(0, core_r - spread_height), 
                          min(self.height, core_r + spread_height + 1)):
                for c in range(max(0, core_c - spread_width),
                              min(self.width, core_c + spread_width + 1)):
                    # Distance from this core
                    dr = (r - core_r) / spread_height if spread_height > 0 else 0
                    dc = (c - core_c) / spread_width if spread_width > 0 else 0
                    dist = math.sqrt(dr**2 + dc**2)
                    
                    if dist <= 1.5:
                        # Irregular falloff (not perfect Gaussian)
                        # Add randomness to simulate turbulent heat spread
                        noise_factor = np.random.uniform(0.85, 1.15)
                        falloff = math.exp(-(dist**2) / 0.8) * noise_factor
                        falloff = max(0, min(1, falloff))  # Clamp to [0, 1]
                        
                        hotspot_temp = core_temp * intensity * falloff
                        
                        # Blend with existing temperature (additive for overlapping cores)
                        frame[r, c] = frame[r, c] + hotspot_temp * 0.6
        
        # Add motion blur effect (camera in motion)
        # Simulate slight directional blur
        blur_direction = np.random.choice(['horizontal', 'vertical', 'diagonal'])
        blur_strength = np.random.randint(1, 3)
        
        if blur_direction == 'horizontal':
            for r in range(max(0, center_row - spread_height), 
                          min(self.height, center_row + spread_height)):
                for c in range(max(0, center_col - spread_width),
                              min(self.width, center_col + spread_width)):
                    if c + blur_strength < self.width:
                        avg_temp = (frame[r, c] + frame[r, c + blur_strength]) / 2
                        frame[r, c] = avg_temp * 0.7 + frame[r, c] * 0.3
        
        elif blur_direction == 'vertical':
            for r in range(max(0, center_row - spread_height), 
                          min(self.height, center_row + spread_height)):
                for c in range(max(0, center_col - spread_width),
                              min(self.width, center_col + spread_width)):
                    if r + blur_strength < self.height:
                        avg_temp = (frame[r, c] + frame[r + blur_strength, c]) / 2
                        frame[r, c] = avg_temp * 0.7 + frame[r, c] * 0.3
        
        # Add scattered heat particles around the fire (reduced distribution)
        num_particles = np.random.randint(3, 8)  # Fewer particles for smaller fires
        for _ in range(num_particles):
            particle_r = center_row + np.random.randint(-spread_height, spread_height + 1)
            particle_c = center_col + np.random.randint(-spread_width, spread_width + 1)
            
            if 0 <= particle_r < self.height and 0 <= particle_c < self.width:
                particle_temp = temperature * np.random.uniform(0.1, 0.4)
                frame[particle_r, particle_c] += particle_temp
        
        # Add gradient halo around fire (heat dissipation) - reduced for smaller fires
        halo_radius = max(spread_width, spread_height) * 1.2  # Smaller halo
        for r in range(max(0, int(center_row - halo_radius)), 
                      min(self.height, int(center_row + halo_radius + 1))):
            for c in range(max(0, int(center_col - halo_radius)),
                          min(self.width, int(center_col + halo_radius + 1))):
                dr = (r - center_row) / halo_radius
                dc = (c - center_col) / halo_radius
                dist = math.sqrt(dr**2 + dc**2)
                
                if 0.5 < dist <= 1.2:
                    # Gentle gradient halo
                    halo_temp = temperature * 0.15 * math.exp(-(dist - 0.5)**2 / 0.3)
                    frame[r, c] += halo_temp * np.random.uniform(0.5, 1.0)
        
        # Round to 2 decimal places to match real MLX90640 sensor precision
        frame = np.round(frame, 2)
        
        return frame
    
    def add_hotspot(self, frame: np.ndarray, center_row: int, center_col: int,
                   size: List[int], temperature: float, intensity: float) -> np.ndarray:
        """Wrapper to use realistic fire hotspot generation"""
        return self.add_realistic_fire_hotspot(frame, center_row, center_col, 
                                              size, temperature, intensity)
    
    def generate_frame(self, drone_lat: float, drone_lon: float,
                      drone_heading: float, timestamp: datetime) -> np.ndarray:
        """Generate a single thermal frame at drone position"""
        # Random ambient temperature within range
        ambient_temp = np.random.uniform(*self.hotspot_config['ambient_temperature_c'])
        
        # Create base frame
        frame = self.create_base_frame(ambient_temp)
        
        # Add hotspots if in view
        for hotspot in self.hotspot_config['locations']:
            # Calculate if hotspot is in camera view
            row, col = self.gps_to_pixel(
                drone_lat, drone_lon,
                hotspot['latitude'], hotspot['longitude'],
                drone_heading
            )
            
            if row >= 0 and col >= 0:
                # Hotspot is in view - add it
                hotspot_temp = np.random.uniform(*hotspot['temperature_c'])
                self.add_hotspot(
                    frame, row, col,
                    hotspot['size_pixels'],
                    hotspot_temp,
                    hotspot['intensity']
                )
        
        return frame
    
    def save_frame_npy(self, frame: np.ndarray, filename: str):
        """Save thermal frame as NPY file"""
        np.save(filename, frame)
    
    def save_frame_csv(self, frame: np.ndarray, filename: str, 
                      timestamp: datetime):
        """Save thermal frame as CSV file with metadata"""
        with open(filename, 'w') as f:
            # Write header
            f.write("# Thermal Frame Data\n")
            f.write(f"# Timestamp:,{timestamp.isoformat()}\n")
            f.write(f"# Min Temp:,{np.min(frame):.2f}\n")
            f.write(f"# Max Temp:,{np.max(frame):.2f}\n")
            f.write(f"# Mean Temp:,{np.mean(frame):.2f}\n")
            f.write(f"# Resolution: {self.height}x{self.width}\n")
            
            # Write data with 2 decimal places to match real MLX90640 sensor
            pd.DataFrame(frame).to_csv(f, header=False, index=False, float_format='%.2f')
    
    def generate_thermal_data(self, gps_telemetry: pd.DataFrame,
                             output_dir: str, session_name: str):
        """Generate thermal data synchronized with GPS telemetry"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"\n[THERMAL]  Generating thermal data...")
        print(f"   Resolution: {self.width}x{self.height}")
        print(f"   Output: {output_path}")
        
        # Thermal capture interval
        interval_sec = self.config['data_collection']['thermal_interval_sec']
        
        # Get start time
        start_time = pd.to_datetime(gps_telemetry['timestamp'].iloc[0])
        
        frame_count = 0
        last_capture_time = start_time - timedelta(seconds=interval_sec)
        
        for idx, row in gps_telemetry.iterrows():
            current_time = pd.to_datetime(row['timestamp'])
            
            # Check if it's time to capture a frame
            if (current_time - last_capture_time).total_seconds() >= interval_sec:
                # Skip frame randomly (simulate missed frames)
                if np.random.random() < self.sim_config['thermal_frame_skip_probability']:
                    continue
                
                # Generate thermal frame
                frame = self.generate_frame(
                    row['latitude'],
                    row['longitude'],
                    row['heading'],
                    current_time
                )
                
                # Create filename
                timestamp_str = current_time.strftime('%Y%m%d_%H%M%S')
                base_filename = f"{session_name}_thermal_{frame_count:04d}_{timestamp_str}"
                
                # Save as NPY
                npy_file = output_path / f"{base_filename}.npy"
                self.save_frame_npy(frame, str(npy_file))
                
                # Save as CSV
                csv_file = output_path / f"{base_filename}.csv"
                self.save_frame_csv(frame, str(csv_file), current_time)
                
                frame_count += 1
                last_capture_time = current_time
                
                if frame_count % 50 == 0:
                    print(f"   Generated {frame_count} frames...")
        
        print(f"   [OK] Generated {frame_count} thermal frames")
        print(f"   [OK] Saved to: {output_path}")
        
        return frame_count


def main():
    """Test thermal generator"""
    from flight_path_calculator import FlightPathCalculator
    from gps_generator import GPSGenerator
    
    # Generate waypoints and GPS data
    calculator = FlightPathCalculator()
    waypoints = calculator.generate_waypoints()
    
    gps_gen = GPSGenerator()
    start_time = datetime.strptime('20251213_140000', '%Y%m%d_%H%M%S')
    gps_telemetry = gps_gen.generate_telemetry(waypoints, start_time)
    
    # Generate thermal data
    thermal_gen = ThermalGenerator()
    
    # Test with first few GPS points
    test_telemetry = gps_telemetry.head(20)
    
    print("\n[STATS] Generating test thermal frames...")
    frame_count = thermal_gen.generate_thermal_data(
        test_telemetry,
        'data/thermal',
        'test_thermal'
    )
    
    print(f"\n[OK] Generated {frame_count} test frames")


if __name__ == '__main__':
    main()
