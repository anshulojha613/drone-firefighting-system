#!/usr/bin/env python3
"""
Field Test Simulation Orchestrator
Main script to generate complete synthetic field test data
"""

import sys
import yaml
from pathlib import Path
from datetime import datetime
import json
import argparse

from flight_path_calculator import FlightPathCalculator
from gps_generator import GPSGenerator
from thermal_generator import ThermalGenerator
from environment_generator import EnvironmentGenerator


class FieldTestSimulator:
    def __init__(self, config_file: str = "simulation_config.yaml"):
        """Initialize field test simulator"""
        self.config_file = config_file
        
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.mission = self.config['mission']
        self.data_collection = self.config['data_collection']
        
        # Initialize generators
        self.flight_calculator = FlightPathCalculator(config_file)
        self.gps_generator = GPSGenerator(config_file)
        self.thermal_generator = ThermalGenerator(config_file)
        self.environment_generator = EnvironmentGenerator(config_file)
        
    def run_simulation(self, output_dir: str = None):
        """Run complete field test simulation"""
        print("\n" + "="*70)
        print("[DRONE] FIELD TEST SIMULATION")
        print("="*70)
        print(f"Mission: {self.mission['name']}")
        print(f"Start time: {self.mission['start_time']}")
        print(f"Description: {self.mission['description']}")
        print("="*70 + "\n")
        
        # Step 1: Calculate flight params
        print("STEP 1: Calculating Flight Parameters")
        print("-" * 70)
        self.flight_calculator.print_summary()
        
        # Step 2: Generate waypoints
        print("\nSTEP 2: Generating Flight Waypoints")
        print("-" * 70)
        waypoints = self.flight_calculator.generate_waypoints()
        print(f"[OK] Generated {len(waypoints)} waypoints")
        
        # Save waypoints
        if output_dir is None:
            output_dir = self.data_collection['output_dir']
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        waypoints_file = output_path / 'waypoints.json'
        with open(waypoints_file, 'w') as f:
            json.dump(waypoints, f, indent=2)
        print(f"[OK] Saved waypoints to: {waypoints_file}")
        
        # Step 3: Generate GPS telemetry
        print("\nSTEP 3: Generating GPS Telemetry")
        print("-" * 70)
        
        start_time = datetime.strptime(
            self.mission['start_time'],
            '%Y%m%d_%H%M%S'
        )
        
        gps_telemetry = self.gps_generator.generate_telemetry(waypoints, start_time)
        
        # Save GPS data
        session_name = f"{self.data_collection['session_prefix']}_{self.mission['start_time']}"
        gps_dir = output_path / 'gps'
        gps_dir.mkdir(exist_ok=True)
        gps_file = gps_dir / f"{session_name}_gps.csv"
        
        self.gps_generator.save_telemetry(gps_telemetry, str(gps_file))
        
        # Step 4: Generate thermal data
        print("\nSTEP 4: Generating Thermal Data")
        print("-" * 70)
        
        thermal_dir = output_path / 'thermal'
        thermal_count = self.thermal_generator.generate_thermal_data(
            gps_telemetry,
            str(thermal_dir),
            session_name
        )
        
        # Step 5: Generate environment data
        print("\nSTEP 5: Generating Environment Data")
        print("-" * 70)
        
        env_dir = output_path / 'environment'
        env_dir.mkdir(exist_ok=True)
        env_file = env_dir / f"{session_name}_environment.csv"
        
        env_data = self.environment_generator.generate_environment_data(
            gps_telemetry,
            str(env_file)
        )
        
        # Step 6: Create summary
        print("\nSTEP 6: Creating Summary Report")
        print("-" * 70)
        
        summary = self.create_summary(
            waypoints, gps_telemetry, thermal_count, env_data
        )
        
        summary_file = output_path / 'logs' / f"{session_name}_summary.json"
        summary_file.parent.mkdir(exist_ok=True)
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"[OK] Saved summary to: {summary_file}")
        
        # Final summary
        print("\n" + "="*70)
        print("[PASS] SIMULATION COMPLETE")
        print("="*70)
        print(f"\n[DIR] Output directory: {output_path.absolute()}")
        print(f"\n[STATS] Generated Data:")
        print(f"   GPS readings:        {len(gps_telemetry)}")
        print(f"   Thermal frames:      {thermal_count}")
        print(f"   Environment readings: {len(env_data)}")
        print(f"   Waypoints:           {len(waypoints)}")
        print(f"\n[TIME]  Mission Duration:    {summary['mission_duration_sec']:.1f}s ({summary['mission_duration_min']:.1f}min)")
        print(f"[BATTERY] Battery Usage:       {summary['battery_usage_percent']:.1f}%")
        print(f" Distance Covered:    {summary['total_distance_m']:.1f}m ({summary['total_distance_miles']:.2f} miles)")
        print(f"\n[FIRE] Hotspots Detected:   {summary['hotspots_in_view']}")
        
        print("\n" + "="*70 + "\n")
        
        return summary
    
    def create_summary(self, waypoints, gps_telemetry, thermal_count, env_data):
        """Create mission summary"""
        # Calculate statistics
        start_time = gps_telemetry['timestamp'].iloc[0]
        end_time = gps_telemetry['timestamp'].iloc[-1]
        duration = (datetime.fromisoformat(end_time) - 
                   datetime.fromisoformat(start_time)).total_seconds()
        
        # Calculate distance
        total_distance = 0
        for i in range(len(gps_telemetry) - 1):
            lat1 = gps_telemetry.iloc[i]['latitude']
            lon1 = gps_telemetry.iloc[i]['longitude']
            lat2 = gps_telemetry.iloc[i+1]['latitude']
            lon2 = gps_telemetry.iloc[i+1]['longitude']
            
            total_distance += self.gps_generator.calculate_distance(
                lat1, lon1, lat2, lon2
            )
        
        # Flight params
        params = self.flight_calculator.calculate_flight_params()
        
        # Check hotspot detection
        hotspots_detected = []
        for hotspot in self.config['hotspots']['locations']:
            for _, row in gps_telemetry.iterrows():
                distance = self.gps_generator.calculate_distance(
                    row['latitude'], row['longitude'],
                    hotspot['latitude'], hotspot['longitude']
                )
                # If within thermal camera range
                if distance < self.config['thermal_camera']['coverage_at_altitude']['width_m'] / 2:
                    if hotspot['name'] not in hotspots_detected:
                        hotspots_detected.append(hotspot['name'])
                    break
        
        summary = {
            'mission_name': self.mission['name'],
            'start_time': start_time,
            'end_time': end_time,
            'mission_duration_sec': duration,
            'mission_duration_min': duration / 60,
            'total_distance_m': total_distance,
            'total_distance_miles': total_distance / 1609.34,
            'battery_usage_percent': params['battery']['usage_percent'],
            'battery_remaining_min': params['battery']['remaining_min'],
            'data_generated': {
                'gps_readings': len(gps_telemetry),
                'thermal_frames': thermal_count,
                'environment_readings': len(env_data),
                'waypoints': len(waypoints)
            },
            'flight_params': {
                'cruise_altitude_ft': self.config['drone']['cruise_altitude_ft'],
                'cruise_speed_ms': self.config['drone']['cruise_speed_ms'],
                'passes_required': params['passes_required'],
                'area_covered_m2': params['area']['area_m2'],
                'area_covered_acres': params['area']['area_acres']
            },
            'hotspots_configured': len(self.config['hotspots']['locations']),
            'hotspots_in_view': len(hotspots_detected),
            'hotspots_detected': hotspots_detected,
            'gps_statistics': {
                'lat_min': float(gps_telemetry['latitude'].min()),
                'lat_max': float(gps_telemetry['latitude'].max()),
                'lon_min': float(gps_telemetry['longitude'].min()),
                'lon_max': float(gps_telemetry['longitude'].max()),
                'alt_min': float(gps_telemetry['altitude'].min()),
                'alt_max': float(gps_telemetry['altitude'].max())
            },
            'environment_statistics': {
                'temp_min': float(env_data['temperature'].min()),
                'temp_max': float(env_data['temperature'].max()),
                'humidity_min': float(env_data['humidity'].min()),
                'humidity_max': float(env_data['humidity'].max())
            }
        }
        
        return summary


def main():
    parser = argparse.ArgumentParser(
        description='Generate synthetic field test data for drone simulation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run simulation with default config
  python simulate_field_test.py
  
  # Use custom config file
  python simulate_field_test.py --config my_config.yaml
  
  # Specify output directory
  python simulate_field_test.py --output /path/to/output
  
  # Show flight params only (no data generation)
  python simulate_field_test.py --dry-run

Output:
  The simulation generates data in the same format as field_testing module:
  - data/gps/simulated_field_test_YYYYMMDD_HHMMSS_gps.csv
  - data/thermal/simulated_field_test_YYYYMMDD_HHMMSS_thermal_NNNN_*.npy
  - data/thermal/simulated_field_test_YYYYMMDD_HHMMSS_thermal_NNNN_*.csv
  - data/environment/simulated_field_test_YYYYMMDD_HHMMSS_environment.csv
  - data/logs/simulated_field_test_YYYYMMDD_HHMMSS_summary.json
        """
    )
    
    parser.add_argument(
        '--config',
        default='simulation_config.yaml',
        help='Configuration file (default: simulation_config.yaml)'
    )
    
    parser.add_argument(
        '--output',
        help='Output directory (default: data/)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show flight params without generating data'
    )
    
    args = parser.parse_args()
    
    # Check if config exists
    if not Path(args.config).exists():
        print(f"[ERROR] Configuration file not found: {args.config}")
        sys.exit(1)
    
    # Initialize simulator
    simulator = FieldTestSimulator(args.config)
    
    if args.dry_run:
        # Just show flight params
        print("\n[SCAN] DRY RUN MODE - Showing flight params only\n")
        simulator.flight_calculator.print_summary()
        waypoints = simulator.flight_calculator.generate_waypoints()
        print(f"\n[LOC] Would generate {len(waypoints)} waypoints")
    else:
        # Run full simulation
        simulator.run_simulation(args.output)


if __name__ == '__main__':
    main()
