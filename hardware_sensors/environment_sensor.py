"""
Environment Sensor Module for Hardware Mode
Reads temperature and humidity from DHT22 and barometric data from Pixhawk
Ported from drone_project/field_testing/sensors/environment_sensor.py
"""

import os
import time
import csv
import json
from datetime import datetime
from pathlib import Path

try:
    import adafruit_dht
    import board
    DHT_AVAILABLE = True
except ImportError:
    DHT_AVAILABLE = False

try:
    from pymavlink import mavutil
    MAVLINK_AVAILABLE = True
except ImportError:
    MAVLINK_AVAILABLE = False


class EnvironmentSensor:
    def __init__(self, config, simulation_mode=False, pixhawk_connection=None):
        """
        Initialize environment sensor
        
        Args:
            config: Configuration dictionary
            simulation_mode: If True, simulate sensor
            pixhawk_connection: Shared Pixhawk connection for barometric data
        """
        self.config = config
        self.simulation_mode = simulation_mode or not DHT_AVAILABLE
        self.sensor = None
        self.pixhawk_connection = pixhawk_connection
        self.last_reading = {
            'temperature': 25.0, 
            'humidity': 50.0,
            'pressure': 1013.25,
            'baro_altitude': 0.0,
            'baro_temperature': 25.0
        }
        self.read_count = 0
        
        # Get output path from config
        env_config = config.get('hardware', {}).get('environment', {})
        self.output_path = env_config.get('output_path', 'data/environment')
        self.log_format = env_config.get('log_format', 'csv')
        
        os.makedirs(self.output_path, exist_ok=True)
        
        if not self.simulation_mode:
            try:
                gpio_pin = env_config.get('gpio_pin', 4)
                
                pin_map = {
                    4: board.D4,
                    17: board.D17,
                    27: board.D27,
                    22: board.D22,
                    23: board.D23,
                    24: board.D24,
                }
                
                pin = pin_map.get(gpio_pin, board.D4)
                self.sensor = adafruit_dht.DHT22(pin, use_pulseio=False)
                print("[OK] Environment sensor initialized (DHT22)")
            except Exception as e:
                print(f"[FAIL] Failed to initialize environment sensor: {e}")
                print("  Falling back to simulation mode")
                self.simulation_mode = True
        else:
            print("[OK] Environment sensor in simulation mode")
    
    def read(self):
        """
        Read temperature, humidity, and barometric data
        
        Returns:
            dict with reading or None on error
        """
        if self.simulation_mode:
            import random
            temp = self.last_reading['temperature'] + random.uniform(-0.5, 0.5)
            humidity = self.last_reading['humidity'] + random.uniform(-2, 2)
            pressure = self.last_reading['pressure'] + random.uniform(-1, 1)
            baro_alt = self.last_reading['baro_altitude'] + random.uniform(-0.2, 0.2)
            baro_temp = self.last_reading['baro_temperature'] + random.uniform(-0.3, 0.3)
            
            temp = max(15, min(35, temp))
            humidity = max(30, min(80, humidity))
            pressure = max(950, min(1050, pressure))
            baro_alt = max(0, baro_alt)
            baro_temp = max(15, min(35, baro_temp))
            
            reading = {
                'temperature': round(temp, 1),
                'humidity': round(humidity, 1),
                'pressure': round(pressure, 2),
                'baro_altitude': round(baro_alt, 2),
                'baro_temperature': round(baro_temp, 1),
                'timestamp': datetime.now().isoformat(),
                'mode': 'simulation'
            }
            self.last_reading = reading
            
        else:
            try:
                temperature = self.sensor.temperature if self.sensor else None
                humidity = self.sensor.humidity if self.sensor else None
                
                pressure = None
                baro_altitude = None
                baro_temperature = None
                
                if self.pixhawk_connection and MAVLINK_AVAILABLE:
                    try:
                        baro_msg = self.pixhawk_connection.recv_match(
                            type='SCALED_PRESSURE', 
                            blocking=False
                        )
                        if baro_msg:
                            pressure = baro_msg.press_abs
                            baro_temperature = baro_msg.temperature / 100.0
                        
                        alt_msg = self.pixhawk_connection.recv_match(
                            type='VFR_HUD',
                            blocking=False
                        )
                        if alt_msg:
                            baro_altitude = alt_msg.alt
                    except Exception as e:
                        print(f"  [WARN] Barometric read error: {e}")
                
                if temperature is not None and humidity is not None:
                    reading = {
                        'temperature': round(temperature, 1),
                        'humidity': round(humidity, 1),
                        'pressure': round(pressure, 2) if pressure is not None else self.last_reading.get('pressure'),
                        'baro_altitude': round(baro_altitude, 2) if baro_altitude is not None else self.last_reading.get('baro_altitude'),
                        'baro_temperature': round(baro_temperature, 1) if baro_temperature is not None else self.last_reading.get('baro_temperature'),
                        'timestamp': datetime.now().isoformat(),
                        'mode': 'hardware'
                    }
                    self.last_reading = reading
                else:
                    reading = self.last_reading.copy()
                    reading['timestamp'] = datetime.now().isoformat()
                    reading['note'] = 'Using last valid reading'
                    
            except RuntimeError as e:
                print(f"  [WARN] DHT22 read error (using last reading): {e}")
                reading = self.last_reading.copy()
                reading['timestamp'] = datetime.now().isoformat()
                reading['note'] = 'Read error, using last valid'
            except Exception as e:
                print(f"  [FAIL] Environment sensor error: {e}")
                return None
        
        self.read_count += 1
        return reading
    
    def log_reading(self, reading, session_name="test"):
        """
        Log reading to file
        
        Args:
            reading: Reading dictionary
            session_name: Session name for filename
        """
        if not reading:
            return
        
        try:
            if self.log_format == 'csv':
                csv_file = os.path.join(self.output_path, f"{session_name}_environment.csv")
                
                file_exists = os.path.exists(csv_file)
                
                with open(csv_file, 'a', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=[
                        'timestamp', 'temperature', 'humidity', 'pressure', 
                        'baro_altitude', 'baro_temperature', 'mode', 'note'
                    ])
                    
                    if not file_exists:
                        writer.writeheader()
                    
                    writer.writerow({
                        'timestamp': reading['timestamp'],
                        'temperature': reading.get('temperature'),
                        'humidity': reading.get('humidity'),
                        'pressure': reading.get('pressure'),
                        'baro_altitude': reading.get('baro_altitude'),
                        'baro_temperature': reading.get('baro_temperature'),
                        'mode': reading.get('mode', 'unknown'),
                        'note': reading.get('note', '')
                    })
                
                print(f"  [OK] Environment: {reading['temperature']}°C, {reading['humidity']}% RH, "
                      f"{reading.get('pressure', 'N/A')} mbar, Alt: {reading.get('baro_altitude', 'N/A')}m")
                
            elif self.log_format == 'json':
                json_file = os.path.join(self.output_path, f"{session_name}_environment.json")
                
                if os.path.exists(json_file):
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                else:
                    data = {'readings': []}
                
                data['readings'].append(reading)
                
                with open(json_file, 'w') as f:
                    json.dump(data, f, indent=2)
                
                print(f"  [OK] Environment: {reading['temperature']}°C, {reading['humidity']}% RH, "
                      f"{reading.get('pressure', 'N/A')} mbar, Alt: {reading.get('baro_altitude', 'N/A')}m")
                
        except Exception as e:
            print(f"  [FAIL] Error logging environment data: {e}")
    
    def get_status(self):
        """Get sensor status"""
        return {
            'sensor': 'Environment (DHT22)',
            'model': 'DHT22',
            'status': 'active' if not self.simulation_mode else 'simulation',
            'reads': self.read_count,
            'last_reading': self.last_reading
        }
    
    def cleanup(self):
        """Cleanup sensor resources"""
        if self.sensor and not self.simulation_mode:
            try:
                self.sensor.exit()
                print("[OK] Environment sensor cleaned up")
            except Exception as e:
                print(f"Error during environment sensor cleanup: {e}")
