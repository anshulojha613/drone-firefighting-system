"""
Scouter Drone (SD) Simulator
Generates field_testing_simulated compatible data with drone controller abstraction
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

# Import data generation modules (now included in project)
from field_testing_simulated.flight_path_calculator import FlightPathCalculator
from field_testing_simulated.gps_generator import GPSGenerator
from field_testing_simulated.thermal_generator import ThermalGenerator
from field_testing_simulated.environment_generator import EnvironmentGenerator

# Import drone controller abstraction
from drone_control import ControllerFactory

# Import camera and fire detection modules
from modules.camera_module import CameraModule
from modules.fire_detector import FireDetector


class ScouterDroneSimulator:
    """
    Scouter drone simulator - generates realistic mission data
    
    Simulates GPS, thermal, and environment data compatible with
    field_testing_simulated module. Used this for 90% of development
    since I couldn't fly the real drone every day.
    
    TODO: Add wind simulation (affects GPS accuracy)
    TODO: Simulate battery drain based on flight distance
    TODO: Add camera gimbal simulation for better thermal coverage
    """
    def __init__(self, task_config: Dict, drone_id: str, output_base_dir: str = 'data', config_path: str = 'config/dfs_config.yaml'):
        self.task_config = task_config
        self.drone_id = drone_id
        self.output_base_dir = output_base_dir
        self.config_path = config_path
        
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
        self.controller = ControllerFactory.create_controller(self.drone_id, self.config_path)
        
        # Hotspot detections
        self.hotspots_detected = []
        
        # Create images directory for still pictures
        os.makedirs(os.path.join(self.session_dir, 'images'), exist_ok=True)
        
        # Load main config for camera and fire detection settings
        self.main_config = self._load_main_config()
        
        # Initialize camera module (for still picture capture)
        self.camera = CameraModule(self.main_config, simulation_mode=True)
        
        # Initialize fire detector (for ML-based confirmation)
        self.fire_detector = FireDetector(self.main_config, simulation_mode=True)
        
        # Validated hotspots (confirmed by ML)
        self.validated_hotspots = []
    
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
                import time
                time.sleep(self.delay_sec)
                self.controller.takeoff(altitude)
                time.sleep(self.delay_sec)
            
            # Generate GPS telemetry from waypoints
            print("   Generating GPS telemetry...")
            start_time = datetime.now()
            gps_data = self.gps_gen.generate_telemetry(waypoints, start_time)
            self._save_gps_data(gps_data)
            
            # Generate environment data
            print("   Generating environment data...")
            env_output_file = os.path.join(
                self.session_dir, 'environment',
                f"{self.session_name}_environment.csv"
            )
            self.env_gen.generate_environment_data(gps_data, env_output_file)
            
            # Generate thermal data
            print("   Generating thermal data...")
            thermal_output_dir = os.path.join(self.session_dir, 'thermal')
            frame_count = self.thermal_gen.generate_thermal_data(
                gps_data, 
                thermal_output_dir, 
                self.session_name
            )
            
            # Capture still images during thermal scan (at regular intervals)
            print("   Capturing still images...")
            images_dir = os.path.join(self.session_dir, 'images')
            self._capture_still_images(gps_data, images_dir)
            
            # Detect hotspots by loading saved thermal frames
            print("   Analyzing thermal data for hotspots...")
            hotspots = self._detect_hotspots(thermal_output_dir, gps_data, frame_count)
            
            # Validate hotspots with ML-based fire detection on still images
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
            # Always disconnect controller
            if self.controller.is_connected():
                self.controller.disconnect()
    
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
