"""
GPS Sensor Module for Hardware Mode
Reads GPS coordinates from Pixhawk via MAVLink
Ported from drone_project/field_testing/sensors/gps_sensor.py
"""

import os
import time
import csv
import json
from datetime import datetime
from pathlib import Path

try:
    from pymavlink import mavutil
    MAVLINK_AVAILABLE = True
except ImportError:
    MAVLINK_AVAILABLE = False


class GPSSensor:
    def __init__(self, config, simulation_mode=False):
        """
        Initialize GPS sensor
        
        Args:
            config: Configuration dictionary
            simulation_mode: If True, simulate GPS
        """
        self.config = config
        self.simulation_mode = simulation_mode or not MAVLINK_AVAILABLE
        self.connection = None
        self.read_count = 0
        
        # Get output path from config
        gps_config = config.get('hardware', {}).get('gps', {})
        self.output_path = gps_config.get('output_path', 'data/gps')
        self.log_format = gps_config.get('log_format', 'csv')
        
        # Simulated GPS state
        self.sim_lat = 33.2265
        self.sim_lon = -96.8265
        self.sim_alt = 0
        self.sim_heading = 0
        
        os.makedirs(self.output_path, exist_ok=True)
        
        if not self.simulation_mode:
            try:
                drone_control_config = config.get('drone_control', {}).get('hardware', {})
                conn_string = drone_control_config.get('connection_string', '/dev/ttyAMA0')
                baud_rate = drone_control_config.get('baud', 57600)
                timeout = gps_config.get('timeout', 10)
                
                print(f"Connecting to Pixhawk on {conn_string}...")
                self.connection = mavutil.mavlink_connection(
                    conn_string,
                    baud=baud_rate,
                    source_system=255
                )
                
                print("Waiting for heartbeat...")
                self.connection.wait_heartbeat(timeout=timeout)
                print("[OK] GPS sensor (Pixhawk) connected")
                
                self.connection.mav.request_data_stream_send(
                    self.connection.target_system,
                    self.connection.target_component,
                    mavutil.mavlink.MAV_DATA_STREAM_ALL,
                    4,
                    1
                )
                
            except Exception as e:
                print(f"[FAIL] Failed to connect to Pixhawk: {e}")
                print("  Falling back to simulation mode")
                self.simulation_mode = True
                self.connection = None
        else:
            print("[OK] GPS sensor in simulation mode")
    
    def read(self):
        """
        Read GPS location
        
        Returns:
            dict with GPS data or None on error
        """
        if self.simulation_mode:
            import random
            self.sim_lat += random.uniform(-0.00001, 0.00001)
            self.sim_lon += random.uniform(-0.00001, 0.00001)
            self.sim_alt += random.uniform(-0.1, 0.1)
            self.sim_heading = (self.sim_heading + random.uniform(-5, 5)) % 360
            
            reading = {
                'timestamp': datetime.now().isoformat(),
                'latitude': self.sim_lat,
                'longitude': self.sim_lon,
                'altitude': max(0, self.sim_alt),
                'heading': self.sim_heading,
                'satellites': 12,
                'fix_type': 3,
                'mode': 'simulation'
            }
            
        else:
            try:
                msg = self.connection.recv_match(type='GPS_RAW_INT', blocking=True, timeout=2)
                
                if msg:
                    reading = {
                        'timestamp': datetime.now().isoformat(),
                        'latitude': msg.lat / 1e7,
                        'longitude': msg.lon / 1e7,
                        'altitude': msg.alt / 1000.0,
                        'satellites': msg.satellites_visible,
                        'fix_type': msg.fix_type,
                        'heading': 0,
                        'mode': 'hardware'
                    }
                    
                    heading_msg = self.connection.recv_match(type='VFR_HUD', blocking=False)
                    if heading_msg:
                        reading['heading'] = heading_msg.heading
                    
                else:
                    print("  [WARN] No GPS data received")
                    return None
                    
            except Exception as e:
                print(f"  [FAIL] Error reading GPS: {e}")
                return None
        
        self.read_count += 1
        return reading
    
    def log_reading(self, reading, session_name="test"):
        """
        Log GPS reading to file
        
        Args:
            reading: Reading dictionary
            session_name: Session name for filename
        """
        if not reading:
            return
        
        try:
            if self.log_format == 'csv':
                csv_file = os.path.join(self.output_path, f"{session_name}_gps.csv")
                
                file_exists = os.path.exists(csv_file)
                
                with open(csv_file, 'a', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=[
                        'timestamp', 'latitude', 'longitude', 'altitude', 
                        'heading', 'satellites', 'fix_type', 'mode'
                    ])
                    
                    if not file_exists:
                        writer.writeheader()
                    
                    writer.writerow(reading)
                
                print(f"  [OK] GPS: {reading['latitude']:.6f}, {reading['longitude']:.6f}, "
                      f"Alt: {reading['altitude']:.1f}m, Sats: {reading.get('satellites', 0)}")
                
            elif self.log_format == 'json':
                json_file = os.path.join(self.output_path, f"{session_name}_gps.json")
                
                if os.path.exists(json_file):
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                else:
                    data = {'readings': []}
                
                data['readings'].append(reading)
                
                with open(json_file, 'w') as f:
                    json.dump(data, f, indent=2)
                
                print(f"  [OK] GPS: {reading['latitude']:.6f}, {reading['longitude']:.6f}, "
                      f"Alt: {reading['altitude']:.1f}m")
                
        except Exception as e:
            print(f"  [FAIL] Error logging GPS data: {e}")
    
    def get_status(self):
        """Get sensor status"""
        return {
            'sensor': 'GPS (Pixhawk)',
            'model': 'Pixhawk 2.4.8',
            'status': 'active' if not self.simulation_mode else 'simulation',
            'reads': self.read_count
        }
    
    def cleanup(self):
        """Cleanup GPS connection"""
        if self.connection and not self.simulation_mode:
            try:
                self.connection.close()
                print("[OK] GPS sensor cleaned up")
            except Exception as e:
                print(f"Error during GPS cleanup: {e}")
