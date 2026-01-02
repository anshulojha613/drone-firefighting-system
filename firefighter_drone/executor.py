"""
Firefighter Drone (FD) Simulator
Executes fire suppression missions with camera and ML-based fire confirmation
"""
import os
import yaml
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import time

# Import camera and fire detection modules
from modules.camera_module import CameraModule
from modules.fire_detector import FireDetector


class FirefighterDroneSimulator:
    """
    Firefighter drone simulator - suppression missions
    
    Simulates flying to fire location, confirming fire with camera,
    deploying suppressant, and verifying effectiveness.
    
    TODO: Add actual suppressant payload simulation
    TODO: Implement multi-pass suppression for larger fires
    TODO: Add wind drift calculation for suppressant deployment
    
    Note: Currently just simulates the process. Real suppressant system
    would need pressure sensors, flow meters, etc.
    """
    def __init__(self, task_config: Dict, drone_id: str, output_base_dir: str = 'data', config_path: str = 'config/dfs_config.yaml'):
        self.task_config = task_config
        self.drone_id = drone_id
        self.output_base_dir = output_base_dir
        self.config_path = config_path
        
        # Load config for simulation delays
        self.delay_sec = 0.3  # Default
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                self.delay_sec = config.get('drone_control', {}).get('demo', {}).get('firefighter_delay_sec', 0.3)
        except Exception:
            pass
        
        # Create session directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.session_name = f"{drone_id}_{timestamp}_suppression"
        self.session_dir = os.path.join(output_base_dir, self.session_name)
        
        os.makedirs(os.path.join(self.session_dir, 'logs'), exist_ok=True)
        os.makedirs(os.path.join(self.session_dir, 'images'), exist_ok=True)
        
        self.suppression_log = []
        
        # Load main config for camera and fire detection settings
        self.main_config = self._load_main_config()
        
        # Initialize camera module (for still picture capture)
        self.camera = CameraModule(self.main_config, simulation_mode=True)
        
        # Initialize fire detector (for ML-based confirmation)
        self.fire_detector = FireDetector(self.main_config, simulation_mode=True)
    
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
    
    def execute_suppression_mission(self, target_lat: float, target_lon: float) -> Tuple[bool, str]:
        """
        Execute fire suppression mission
        
        Flies to target, confirms fire, deploys suppressant, verifies.
        Uses ML model to confirm fire before and after suppression.
        
        Known limitation: Doesn't account for fire spread during flight time.
        In real scenario, fire could grow significantly in 2-3 minutes.
        """
        print(f"\n[DRONE] {self.drone_id} - Starting suppression mission")
        print(f"   Target: ({target_lat:.6f}, {target_lon:.6f})")
        
        images_dir = os.path.join(self.session_dir, 'images')
        
        # Simulate flight to target
        print("   Flying to target location...")
        time.sleep(self.delay_sec)
        
        # Capture pre-suppression image for fire confirmation
        print("   Capturing pre-suppression image...")
        time.sleep(self.delay_sec)
        pre_image_path = os.path.join(images_dir, f"{self.session_name}_pre_suppression.jpg")
        fire_confirmed = False
        
        if self.camera.capture_still(pre_image_path):
            # Confirm fire presence with ML
            result = self.fire_detector.detect_fire_in_image(pre_image_path)
            fire_confirmed = result.get('detected', False)
            self.suppression_log.append({
                'timestamp': datetime.now().isoformat(),
                'event': 'pre_suppression_check',
                'fire_detected': fire_confirmed,
                'confidence': result.get('confidence', 0.0)
            })
        
        # Simulate suppression
        print("   Deploying fire suppressant...")
        time.sleep(self.delay_sec * 2)
        
        # Capture post-suppression image to verify effectiveness
        print("   Capturing post-suppression image...")
        time.sleep(self.delay_sec)
        post_image_path = os.path.join(images_dir, f"{self.session_name}_post_suppression.jpg")
        
        # Check if fire is still present after suppression
        suppression_effective = True
        if self.camera.capture_still(post_image_path):
            print("   Verifying suppression effectiveness...")
            result = self.fire_detector.detect_fire_in_image(post_image_path)
            if result.get('detected', False):
                suppression_effective = False
                print(f"   [WARN]  Fire still detected after suppression! Confidence: {result.get('confidence', 0.0):.2f}")
            else:
                print("   [OK] Fire no longer detected - suppression effective")
        
        # Log suppression event
        suppression_event = {
            'timestamp': datetime.now().isoformat(),
            'drone_id': self.drone_id,
            'target_latitude': target_lat,
            'target_longitude': target_lon,
            'suppressant_deployed_kg': 2.5,
            'success': True,
            'fire_confirmed_before': fire_confirmed,
            'suppression_effective': suppression_effective,
            'pre_suppression_image': pre_image_path,
            'post_suppression_image': post_image_path
        }
        
        self.suppression_log.append(suppression_event)
        
        # Save log
        log_file = os.path.join(self.session_dir, 'logs', 'suppression_log.txt')
        with open(log_file, 'w') as f:
            f.write(f"Firefighter Drone Suppression Mission\n")
            f.write(f"{'='*50}\n")
            f.write(f"Drone: {self.drone_id}\n")
            f.write(f"Target: ({target_lat:.6f}, {target_lon:.6f})\n")
            f.write(f"Time: {suppression_event['timestamp']}\n")
            f.write(f"Suppressant Deployed: {suppression_event['suppressant_deployed_kg']} kg\n")
            f.write(f"Fire Confirmed (ML): {fire_confirmed}\n")
            f.write(f"Suppression Effective: {suppression_effective}\n")
            f.write(f"Pre-Suppression Image: {pre_image_path}\n")
            f.write(f"Post-Suppression Image: {post_image_path}\n")
            f.write(f"Status: SUCCESS\n")
        
        # Save detailed JSON log
        json_log_file = os.path.join(self.session_dir, 'logs', 'suppression_log.json')
        with open(json_log_file, 'w') as f:
            json.dump(suppression_event, f, indent=2, default=str)
        
        print(f"[OK] Suppression complete (Fire confirmed: {fire_confirmed}, Effective: {suppression_effective})")
        print(f"   Data saved to: {self.session_dir}")
        
        return True, self.session_dir
    
    def _capture_image(self, lat: float, lon: float, prefix: str, images_dir: str) -> str:
        """Capture a still image at the given location"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        image_filename = f"{self.session_name}_{prefix}_{timestamp}.jpg"
        image_path = os.path.join(images_dir, image_filename)
        
        success = self.camera.capture_still(image_path)
        
        if success:
            # Save metadata
            metadata = {
                'image_path': image_path,
                'latitude': lat,
                'longitude': lon,
                'timestamp': timestamp,
                'type': prefix
            }
            metadata_path = image_path.replace('.jpg', '_metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            return image_path
        
        return None
    
    def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'camera') and self.camera:
            self.camera.cleanup()
