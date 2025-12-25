#!/usr/bin/env python3
"""
Environment Sensor Data Generator
Generates realistic DHT22 and BMP280 sensor data
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
import yaml


class EnvironmentGenerator:
    def __init__(self, config_file: str = "simulation_config.yaml"):
        """Initialize environment generator with config"""
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.env_config = self.config['environment']
        self.sim_config = self.config['simulation']
        
        # Set random seed
        if self.sim_config.get('random_seed'):
            np.random.seed(self.sim_config['random_seed'])
    
    def generate_temperature(self, base_temp: float, variation: float) -> float:
        """Generate temperature reading with natural variation"""
        temp = np.random.uniform(
            base_temp - variation,
            base_temp + variation
        )
        
        # Add sensor noise
        noise = np.random.normal(0, self.env_config['dht22']['accuracy_temp_c'])
        
        return round(temp + noise, 1)
    
    def generate_humidity(self, base_humidity: float, variation: float) -> float:
        """Generate humidity reading with natural variation"""
        humidity = np.random.uniform(
            base_humidity - variation,
            base_humidity + variation
        )
        
        # Add sensor noise
        noise = np.random.normal(0, self.env_config['dht22']['accuracy_humidity'])
        
        # Clamp to valid range
        return round(max(0, min(100, humidity + noise)), 1)
    
    def generate_pressure(self, base_pressure: float, variation: float,
                         altitude: float) -> float:
        """Generate barometric pressure reading"""
        pressure = np.random.uniform(
            base_pressure - variation,
            base_pressure + variation
        )
        
        # Adjust for altitude (approximate)
        # Pressure decreases ~12 Pa per meter
        altitude_adjustment = -altitude * 0.12
        pressure += altitude_adjustment / 100  # Convert Pa to hPa
        
        # Add sensor noise
        noise = np.random.normal(0, self.env_config['bmp280']['accuracy_pressure'])
        
        return round(pressure + noise, 2)
    
    def calculate_barometric_altitude(self, pressure_hpa: float,
                                     sea_level_pressure: float = 1013.25) -> float:
        """Calculate altitude from barometric pressure"""
        # Barometric formula
        altitude = 44330 * (1 - (pressure_hpa / sea_level_pressure) ** 0.1903)
        
        # Add sensor noise
        noise = np.random.normal(0, self.env_config['bmp280']['accuracy_altitude'])
        
        return round(altitude + noise, 2)
    
    def generate_environment_data(self, gps_telemetry: pd.DataFrame,
                                 output_file: str):
        """Generate environment sensor data synchronized with GPS"""
        print(f"\n[ENV]  Generating environment data...")
        
        # Environment capture interval
        interval_sec = self.config['data_collection']['environment_interval_sec']
        
        # Get start time
        start_time = pd.to_datetime(gps_telemetry['timestamp'].iloc[0])
        
        # Base values
        temp_range = self.env_config['dht22']['temperature_range_c']
        base_temp = np.mean(temp_range)
        temp_variation = self.env_config['dht22']['temperature_variation_c']
        
        humidity_range = self.env_config['dht22']['humidity_percent']
        base_humidity = np.mean(humidity_range)
        humidity_variation = self.env_config['dht22']['humidity_variation']
        
        base_pressure = self.env_config['bmp280']['pressure_hpa']
        pressure_variation = self.env_config['bmp280']['pressure_variation']
        
        bmp_temp = self.env_config['bmp280']['temperature_c']
        
        readings = []
        last_capture_time = start_time - timedelta(seconds=interval_sec)
        last_valid_reading = None
        
        for idx, row in gps_telemetry.iterrows():
            current_time = pd.to_datetime(row['timestamp'])
            
            # Check if it's time to capture
            if (current_time - last_capture_time).total_seconds() >= interval_sec:
                # Simulate read error
                if np.random.random() < self.sim_config['environment_read_error_probability']:
                    # Use last valid reading with note
                    if last_valid_reading:
                        reading = last_valid_reading.copy()
                        reading['timestamp'] = current_time.isoformat()
                        reading['mode'] = 'unknown'
                        reading['note'] = 'Read error, using last valid'
                        readings.append(reading)
                    continue
                
                # Generate new reading
                temperature = self.generate_temperature(base_temp, temp_variation)
                humidity = self.generate_humidity(base_humidity, humidity_variation)
                pressure = self.generate_pressure(base_pressure, pressure_variation, 
                                                 row['altitude'])
                baro_altitude = self.calculate_barometric_altitude(pressure)
                
                reading = {
                    'timestamp': current_time.isoformat(),
                    'temperature': temperature,
                    'humidity': humidity,
                    'pressure': pressure,
                    'baro_altitude': baro_altitude,
                    'baro_temperature': bmp_temp + np.random.normal(0, 0.2),
                    'mode': 'simulated',
                    'note': ''
                }
                
                readings.append(reading)
                last_valid_reading = reading
                last_capture_time = current_time
        
        # Convert to DataFrame
        df = pd.DataFrame(readings)
        
        # Save to CSV
        df.to_csv(output_file, index=False)
        
        print(f"   [OK] Generated {len(df)} environment readings")
        print(f"   [OK] Saved to: {output_file}")
        
        return df


def main():
    """Test environment generator"""
    from flight_path_calculator import FlightPathCalculator
    from gps_generator import GPSGenerator
    
    # Generate waypoints and GPS data
    calculator = FlightPathCalculator()
    waypoints = calculator.generate_waypoints()
    
    gps_gen = GPSGenerator()
    start_time = datetime.strptime('20251213_140000', '%Y%m%d_%H%M%S')
    gps_telemetry = gps_gen.generate_telemetry(waypoints, start_time)
    
    # Generate environment data
    env_gen = EnvironmentGenerator()
    env_data = env_gen.generate_environment_data(
        gps_telemetry,
        'data/environment/test_environment.csv'
    )
    
    print("\n[STATS] Sample environment data:")
    print(env_data.head(10))
    
    print(f"\n Statistics:")
    print(f"   Temperature: {env_data['temperature'].min():.1f}°C to {env_data['temperature'].max():.1f}°C")
    print(f"   Humidity: {env_data['humidity'].min():.1f}% to {env_data['humidity'].max():.1f}%")
    print(f"   Pressure: {env_data['pressure'].min():.2f} to {env_data['pressure'].max():.2f} hPa")


if __name__ == '__main__':
    main()
