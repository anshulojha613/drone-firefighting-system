"""
Scouter Drone (SD) Executor
Executes missions using hardware sensors in HW mode or simulation in demo mode
"""
import os
import sys
import yaml
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import csv
import math
import time

# Import data generation modules for simulation mode
from field_testing_simulated.flight_path_calculator import FlightPathCalculator
from field_testing_simulated.gps_generator import GPSGenerator
from field_testing_simulated.thermal_generator import ThermalGenerator
from field_testing_simulated.environment_generator import EnvironmentGenerator

# Import drone controller abstraction
from drone_control import ControllerFactory

# Import hardware sensors for HW mode
from hardware_sensors import CameraSensor, ThermalSensor, EnvironmentSensor, GPSSensor

# Import camera and fire detection modules
from modules.camera_module import CameraModule
from modules.fire_detector import FireDetector


class ScouterDroneSimulator:
    """
    Scouter drone executor - runs missions with hardware or simulation
    
    In HW mode: Uses actual sensors (MLX90640, DHT22, Pixhawk GPS, rpicam)
    In Demo mode: Uses simulation generators for testing
    
    Automatically detects mode from drone controller configuration
    """
    def __init__(self, task_config: Dict, drone_id: str, output_base_dir: str = 'data', config_path: str = 'config/dfs_config.yaml', mode_override: str = None):
        self.task_config = task_config
        self.drone_id = drone_id
        self.output_base_dir = output_base_dir
        self.config_path = config_path
        self.mode_override = mode_override
        
        # Load config for simulation delays
        self.delay_sec = 0.5  # Default
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                self.delay_sec = config.get('drone_control', {}).get('demo', {}).get('scouter_delay_sec', 0.5)
        except Exception:
            pass
        
        # Create session directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.session_name = f"{drone_id}_{timestamp}"
        self.session_dir = os.path.join(output_base_dir, self.session_name)
        
        # Create output directories
        os.makedirs(os.path.join(self.session_dir, 'gps'), exist_ok=True)
        os.makedirs(os.path.join(self.session_dir, 'thermal'), exist_ok=True)
        os.makedirs(os.path.join(self.session_dir, 'environment'), exist_ok=True)
        os.makedirs(os.path.join(self.session_dir, 'logs'), exist_ok=True)
        
        # Build simulation config compatible with field_testing_simulated
        self.sim_config = self._build_simulation_config()
        
        # Write config to temp file for generators (they expect file path)
        self.config_file = os.path.join(self.session_dir, 'sim_config.yaml')
        with open(self.config_file, 'w') as f:
            yaml.dump(self.sim_config, f)
        
        # Initialize generators with config file path
        self.flight_calc = FlightPathCalculator(self.config_file)
        self.gps_gen = GPSGenerator(self.config_file)
        self.thermal_gen = ThermalGenerator(self.config_file)
        self.env_gen = EnvironmentGenerator(self.config_file)
        
        # Initialize drone controller (demo or hardware based on config)
        self.controller = ControllerFactory.create_controller(self.drone_id, self.config_path, mode_override=self.mode_override)
        
        # Hotspot detections
        self.hotspots_detected = []
        
        # Create images directory for still pictures
        os.makedirs(os.path.join(self.session_dir, 'images'), exist_ok=True)
        
        # Load main config for camera and fire detection settings
        self.main_config = self._load_main_config()
        
        # Determine if we're in hardware or simulation mode
        self.is_hardware_mode = self._is_hardware_mode()
        
        # Initialize sensors based on mode
        if self.is_hardware_mode:
            print("[HW] Initializing hardware sensors...")
            self.hw_camera = CameraSensor(self.main_config, simulation_mode=False)
            self.hw_thermal = ThermalSensor(self.main_config, simulation_mode=False)
            self.hw_environment = EnvironmentSensor(self.main_config, simulation_mode=False, 
                                                   pixhawk_connection=None)  # Will get from GPS sensor
            self.hw_gps = GPSSensor(self.main_config, simulation_mode=False)
            
            # Share Pixhawk connection with environment sensor for barometric data
            if hasattr(self.hw_gps, 'connection') and self.hw_gps.connection:
                self.hw_environment.pixhawk_connection = self.hw_gps.connection
            
            # Still need camera module for compatibility
            self.camera = CameraModule(self.main_config, simulation_mode=False)
        else:
            print("[DEMO] Initializing simulation mode...")
            self.hw_camera = None
            self.hw_thermal = None
            self.hw_environment = None
            self.hw_gps = None
            self.camera = CameraModule(self.main_config, simulation_mode=True)
        
        # Initialize fire detector (for ML-based confirmation)
        self.fire_detector = FireDetector(self.main_config, simulation_mode=not self.is_hardware_mode)
        
        # Validated hotspots (confirmed by ML)
        self.validated_hotspots = []
    
    def _is_hardware_mode(self) -> bool:
        """Check if we're running in hardware mode"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            mode = config.get('drone_control', {}).get('mode', 'demo')
            return mode == 'hardware'
        except Exception:
            return False
    
    def _load_main_config(self) -> Dict:
        """Load main DFS config for camera and fire detection settings"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Ensure required sections exist with defaults
            if 'hardware' not in config:
                config['hardware'] = {}
            if 'camera' not in config['hardware']:
                config['hardware']['camera'] = {
                    'resolution': [1920, 1080],
                    'rotation': 0,
                    'video_duration': 10
                }
            if 'fire_detection' not in config:
                config['fire_detection'] = {
                    'image_recognition': {
                        'input_size': [224, 224],
                        'confidence_threshold': 0.7,
                        'model_path': None,
                        'simulation_objects': ['fire', 'smoke']
                    }
                }
            
            return config
        except Exception as e:
            print(f"Warning: Could not load main config: {e}")
            # Return default config
            return {
                'hardware': {
                    'camera': {
                        'resolution': [1920, 1080],
                        'rotation': 0,
                        'video_duration': 10
                    }
                },
                'fire_detection': {
                    'image_recognition': {
                        'input_size': [224, 224],
                        'confidence_threshold': 0.7,
                        'model_path': None,
                        'simulation_objects': ['fire', 'smoke']
                    }
                }
            }
    
    def _build_simulation_config(self) -> Dict:
        """Build simulation config from task params"""
        config = {
            'mission': {
                'name': self.session_name,
                'start_time': datetime.now().strftime('%Y%m%d_%H%M%S'),
                'description': f'Scouter drone {self.drone_id} mission'
            },
            'flight_area': {
                'corner_a': {
                    'latitude': self.task_config['corner_a_lat'],
                    'longitude': self.task_config['corner_a_lon']
                },
                'corner_b': {
                    'latitude': self.task_config['corner_b_lat'],
                    'longitude': self.task_config['corner_b_lon']
                },
                'corner_c': {
                    'latitude': self.task_config['corner_c_lat'],
                    'longitude': self.task_config['corner_c_lon']
                },
                'corner_d': {
                    'latitude': self.task_config['corner_d_lat'],
                    'longitude': self.task_config['corner_d_lon']
                },
                'pattern': self.task_config.get('pattern', 'serpentine'),
                'direction': 'east_west_then_north_south'
            },
            'drone': {
                'cruise_altitude_ft': self.task_config['cruise_altitude_m'] * 3.28084,
                'cruise_altitude_m': self.task_config['cruise_altitude_m'],
                'cruise_speed_ms': self.task_config['cruise_speed_ms'],
                'max_speed_ms': 8.0,
                'ascent_rate_ms': 2.0,
                'descent_rate_ms': 1.5,
                'battery_capacity_mah': 5000,
                'max_flight_time_min': 20,
                'wind': {'enabled': False}
            },
            'thermal_camera': {
                'model': 'MLX90640-D110',
                'resolution': {'width': 32, 'height': 24},
                'field_of_view': {'horizontal_deg': 110, 'vertical_deg': 75},
                'coverage_at_altitude': {
                    'altitude_ft': 50,
                    'altitude_m': 15.24,
                    'width_m': 34.8,
                    'height_m': 23.2
                },
                'overlap': {
                    'recommended_percent': 30,
                    'lateral_percent': 30,
                    'forward_percent': 30
                },
                'effective_coverage': {
                    'width_m': 24.4,
                    'height_m': 16.2
                },
                'refresh_rate_hz': 8,
                'temperature_range_c': [-40, 300],
                'accuracy_c': 1.0,
                'noise_c': 0.5
            },
            'hotspots': {
                'ambient_temperature_c': [15, 17],
                'hotspot_threshold_c': 50,
                'locations': []
            },
            'gps': {
                'update_rate_hz': 1,
                'accuracy_m': 2.5,
                'satellites': [8, 14],
                'fix_type': 3,
                'noise': {'horizontal_m': 0.5, 'vertical_m': 0.5, 'heading_deg': 0.5}
            },
            'environment': {
                'update_rate_hz': 1,
                'dht22': {
                    'temperature_range_c': [11, 13],
                    'temperature_variation_c': 0.1,
                    'humidity_percent': [40, 50],
                    'humidity_variation': 0.15,
                    'accuracy_temp_c': 0.10,
                    'accuracy_humidity': 0.15
                },
                'bmp280': {
                    'pressure_hpa': 995.0,
                    'pressure_variation': 0.5,
                    'altitude_m': 184.0,
                    'temperature_c': 34.0,
                    'accuracy_pressure': 0.12,
                    'accuracy_altitude': 1.0
                }
            },
            'data_collection': {
                'gps_interval_sec': 1,
                'thermal_interval_sec': 1,
                'environment_interval_sec': 1,
                'formats': {'gps': 'csv', 'thermal': 'both', 'environment': 'csv'},
                'output_dir': self.session_dir,
                'session_prefix': self.session_name
            },
            'simulation': {
                'add_sensor_noise': True,
                'add_gps_drift': True,
                'add_wind_effects': False,
                'add_thermal_noise': True,
                'gps_dropout_probability': 0.01,
                'thermal_frame_skip_probability': 0.005,
                'environment_read_error_probability': 0.02,
                'random_seed': None
            }
        }
        
        return config
    
    def execute_mission(self) -> Tuple[int, str]:
        """Run scouting mission and generate data"""
        print(f"\n[DRONE] {self.drone_id} - Starting mission: {self.session_name}")
        print(f"   Mode: {'HARDWARE' if self.is_hardware_mode else 'SIMULATION'}")
        
        try:
            # Connect to drone controller
            if not self.controller.connect():
                raise Exception(f"Failed to connect to drone controller for {self.drone_id}")
            
            # Set home position (first corner of flight area)
            home_lat = self.task_config['corner_a_lat']
            home_lon = self.task_config['corner_a_lon']
            if hasattr(self.controller, 'set_home_position'):
                self.controller.set_home_position(home_lat, home_lon, 0.0)
            
            # Generate waypoints using flight path calculator
            print("   Generating flight path...")
            waypoints = self.flight_calc.generate_waypoints()
            
            # Arm and takeoff
            altitude = self.task_config['cruise_altitude_m']
            if self.controller.arm():
                time.sleep(self.delay_sec)
                self.controller.takeoff(altitude)
                time.sleep(self.delay_sec)
            
            # Execute mission based on mode
            if self.is_hardware_mode:
                gps_data, frame_count = self._execute_hardware_mission(waypoints)
            else:
                gps_data, frame_count = self._execute_simulation_mission(waypoints)
            
            # Capture still images during mission
            print("   Capturing still images...")
            images_dir = os.path.join(self.session_dir, 'images')
            self._capture_still_images(gps_data, images_dir)
            
            # Detect hotspots from thermal data
            print("   Analyzing thermal data for hotspots...")
            thermal_output_dir = os.path.join(self.session_dir, 'thermal')
            hotspots = self._detect_hotspots(thermal_output_dir, gps_data, frame_count)
            
            # Validate hotspots with ML-based fire detection
            print("   Validating hotspots with visual confirmation...")
            self._validate_hotspots_with_ml(hotspots, images_dir)
            
            # Land and disarm
            self.controller.land()
            self.controller.disarm()
            
            validated_count = len([h for h in self.validated_hotspots if h.get('validated', False)])
            print(f"[OK] Mission complete - {len(hotspots)} hotspots detected, {validated_count} validated by ML")
            print(f"   Data saved to: {self.session_dir}")
            
            return len(hotspots), self.session_dir
            
        finally:
            # Cleanup sensors
            if self.is_hardware_mode:
                if self.hw_camera:
                    self.hw_camera.cleanup()
                if self.hw_thermal:
                    self.hw_thermal.cleanup()
                if self.hw_environment:
                    self.hw_environment.cleanup()
                if self.hw_gps:
                    self.hw_gps.cleanup()
            
            # Always disconnect controller
            if self.controller.is_connected():
                self.controller.disconnect()
    
    def _execute_hardware_mission(self, waypoints: List) -> Tuple[pd.DataFrame, int]:
        """Execute mission using actual hardware sensors"""
        print("   [HW] Collecting data from hardware sensors...")
        
        gps_readings = []
        thermal_frames = []
        env_readings = []
        
        start_time = datetime.now()
        frame_count = 0
        
        # Collect data at each waypoint
        for i, waypoint in enumerate(waypoints):
            # Read GPS from Pixhawk
            gps_reading = self.hw_gps.read()
            if gps_reading:
                gps_readings.append(gps_reading)
                self.hw_gps.log_reading(gps_reading, self.session_name)
            
            # Capture thermal frame
            thermal_output_dir = os.path.join(self.session_dir, 'thermal')
            thermal_info = self.hw_thermal.capture(thermal_output_dir, self.session_name)
            if thermal_info:
                thermal_frames.append(thermal_info)
                frame_count += 1
            
            # Read environment data
            env_reading = self.hw_environment.read()
            if env_reading:
                env_readings.append(env_reading)
                self.hw_environment.log_reading(env_reading, self.session_name)
            
            # Small delay between readings
            time.sleep(0.5)
        
        # Convert GPS readings to DataFrame
        if gps_readings:
            gps_data = pd.DataFrame(gps_readings)
        else:
            # Fallback to simulated data if no GPS
            print("   [WARN] No GPS data collected, using simulated data")
            gps_data = self.gps_gen.generate_telemetry(waypoints, start_time)
        
        self._save_gps_data(gps_data)
        
        print(f"   [HW] Collected {len(gps_readings)} GPS readings, {frame_count} thermal frames, {len(env_readings)} env readings")
        
        return gps_data, frame_count
    
    def _execute_simulation_mission(self, waypoints: List) -> Tuple[pd.DataFrame, int]:
        """Execute mission using simulation generators"""
        print("   [DEMO] Generating simulated sensor data...")
        
        # Generate GPS telemetry from waypoints
        start_time = datetime.now()
        gps_data = self.gps_gen.generate_telemetry(waypoints, start_time)
        self._save_gps_data(gps_data)
        
        # Generate environment data
        env_output_file = os.path.join(
            self.session_dir, 'environment',
            f"{self.session_name}_environment.csv"
        )
        self.env_gen.generate_environment_data(gps_data, env_output_file)
        
        # Generate thermal data
        thermal_output_dir = os.path.join(self.session_dir, 'thermal')
        frame_count = self.thermal_gen.generate_thermal_data(
            gps_data, 
            thermal_output_dir, 
            self.session_name
        )
        
        return gps_data, frame_count
    
    def _save_gps_data(self, gps_data: pd.DataFrame):
        """Save GPS data in field_testing_simulated format"""
        output_file = os.path.join(
            self.session_dir, 'gps',
            f"{self.session_name}_gps.csv"
        )
        gps_data.to_csv(output_file, index=False)
    
    def _save_environment_data(self, env_data: pd.DataFrame):
        """Save environment data in field_testing_simulated format"""
        output_file = os.path.join(
            self.session_dir, 'environment',
            f"{self.session_name}_environment.csv"
        )
        env_data.to_csv(output_file, index=False)
    
    def _save_thermal_data(self, thermal_frames: List[Dict]):
        """Save thermal data in field_testing_simulated format"""
        thermal_dir = os.path.join(self.session_dir, 'thermal')
        
        for frame in thermal_frames:
            timestamp = frame['timestamp']
            frame_num = frame['frame_number']
            
            # Save NPY file
            npy_file = os.path.join(
                thermal_dir,
                f"{self.session_name}_thermal_{frame_num:04d}_{timestamp.strftime('%Y%m%d_%H%M%S')}.npy"
            )
            np.save(npy_file, frame['data'])
            
            # Save CSV file
            csv_file = npy_file.replace('.npy', '.csv')
            np.savetxt(csv_file, frame['data'], delimiter=',', fmt='%.2f')
    
    def _detect_hotspots(self, thermal_dir: str, gps_data: pd.DataFrame, frame_count: int) -> List[Dict]:
        """Detect hotspots from saved thermal data"""
        hotspots = []
        threshold = 50.0  # Temperature threshold in Celsius
        
        # Load and analyze each thermal frame
        for i in range(frame_count):
            if i >= len(gps_data):
                break
            
            # Find the thermal frame file (they're saved with timestamps)
            frame_files = sorted([f for f in os.listdir(thermal_dir) if f.endswith('.npy')])
            if i >= len(frame_files):
                break
            
            # Load thermal frame
            frame_file = os.path.join(thermal_dir, frame_files[i])
            thermal_data = np.load(frame_file)
            max_temp = np.max(thermal_data)
            
            if max_temp >= threshold:
                # Get GPS coordinates for this frame
                gps_row = gps_data.iloc[i]
                
                hotspot = {
                    'latitude': gps_row['latitude'],
                    'longitude': gps_row['longitude'],
                    'altitude': gps_row['altitude'],
                    'temperature_c': float(max_temp),
                    'timestamp': gps_row['timestamp'],
                    'frame_number': i,
                    'confidence': 0.85
                }
                
                hotspots.append(hotspot)
                self.hotspots_detected.append(hotspot)
        
        return hotspots
    
    def _capture_still_images(self, gps_data: pd.DataFrame, images_dir: str):
        """Capture still images at regular intervals during the mission"""
        # Capture an image every N waypoints (configurable)
        capture_interval = max(1, len(gps_data) // 10)  # ~10 images per mission
        
        for i in range(0, len(gps_data), capture_interval):
            gps_row = gps_data.iloc[i]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Generate image filename with GPS coordinates
            image_filename = f"{self.session_name}_img_{i:04d}_{timestamp}.jpg"
            image_path = os.path.join(images_dir, image_filename)
            
            # Capture still image
            success = self.camera.capture_still(image_path)
            
            if success:
                # Save metadata for the image
                metadata = {
                    'image_path': image_path,
                    'frame_number': i,
                    'latitude': gps_row['latitude'],
                    'longitude': gps_row['longitude'],
                    'altitude': gps_row['altitude'],
                    'timestamp': timestamp
                }
                
                # Save metadata to JSON
                metadata_path = image_path.replace('.jpg', '_metadata.json')
                import json
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
    
    def _validate_hotspots_with_ml(self, hotspots: List[Dict], images_dir: str):
        """Validate detected hotspots using ML-based fire detection on still images"""
        if not hotspots:
            return
        
        # Get list of captured images
        image_files = sorted([f for f in os.listdir(images_dir) if f.endswith('.jpg')])
        
        if not image_files:
            print("   No still images available for validation")
            return
        
        for hotspot in hotspots:
            frame_num = hotspot.get('frame_number', 0)
            
            # Find the closest image to this hotspot's frame
            closest_image = None
            min_diff = float('inf')
            
            for img_file in image_files:
                # Extract frame number from filename (format: session_img_XXXX_timestamp.jpg)
                try:
                    parts = img_file.split('_')
                    img_frame = int(parts[-2])
                    diff = abs(img_frame - frame_num)
                    if diff < min_diff:
                        min_diff = diff
                        closest_image = img_file
                except (ValueError, IndexError):
                    continue
            
            if closest_image:
                image_path = os.path.join(images_dir, closest_image)
                
                # Create thermal result dict for validation
                thermal_result = {
                    'detected': True,
                    'max_temperature': hotspot.get('temperature_c', 0),
                    'latitude': hotspot.get('latitude'),
                    'longitude': hotspot.get('longitude')
                }
                
                # Validate using fire detector
                validation_result = self.fire_detector.validate_fire_detection(
                    thermal_result, 
                    image_path
                )
                
                # Add validation result to hotspot
                hotspot['ml_validated'] = validation_result.get('validated', False)
                hotspot['ml_confidence'] = validation_result.get('combined_confidence', 0)
                hotspot['validation_image'] = image_path
                hotspot['validation_result'] = validation_result
                
                # Add to validated hotspots list
                validated_hotspot = {**hotspot, **validation_result}
                self.validated_hotspots.append(validated_hotspot)
            else:
                hotspot['ml_validated'] = False
                hotspot['ml_confidence'] = 0
                hotspot['validation_image'] = None
    
    def get_hotspots(self) -> List[Dict]:
        """Get detected hotspots"""
        return self.hotspots_detected
    
    def get_validated_hotspots(self) -> List[Dict]:
        """Get hotspots that have been validated by ML"""
        return [h for h in self.validated_hotspots if h.get('validated', False)]
    
    def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'camera') and self.camera:
            self.camera.cleanup()
        
        if self.is_hardware_mode:
            if self.hw_camera:
                self.hw_camera.cleanup()
            if self.hw_thermal:
                self.hw_thermal.cleanup()
            if self.hw_environment:
                self.hw_environment.cleanup()
            if self.hw_gps:
                self.hw_gps.cleanup()
