"""
Camera Module - Arducam IMX708
Handles still image and video capture
"""

import time
import os
from datetime import datetime
from pathlib import Path

try:
    from picamera2 import Picamera2
    from picamera2.encoders import H264Encoder
    from picamera2.outputs import FileOutput
    CAMERA_AVAILABLE = True
except ImportError:
    CAMERA_AVAILABLE = False
    print("Warning: Camera libraries not available. Running in simulation mode.")


class CameraModule:
    """Handles still image and video capture from Arducam IMX708 or simulation."""
    
    def __init__(self, config, simulation_mode=False):
        self.config = config
        self.simulation_mode = simulation_mode or not CAMERA_AVAILABLE
        self.camera = None
        self.is_recording = False
        self.current_video_path = None
        
        if not self.simulation_mode:
            try:
                self.camera = Picamera2()
                
                # Configure camera
                camera_config = self.camera.create_still_config(
                    main={"size": tuple(config['hardware']['camera']['resolution'])},
                    buffer_count=2
                )
                self.camera.configure(camera_config)
                
                # Set rotation if needed
                rotation = config['hardware']['camera'].get('rotation', 0)
                if rotation:
                    self.camera.set_controls({"Rotation": rotation})
                
                self.camera.start()
                time.sleep(2)  # Allow camera to warm up
                
                print("[OK] Camera initialized OK")
            except Exception as e:
                print(f"[FAIL] Failed to initialize camera: {e}")
                print("  Falling back to simulation mode")
                self.simulation_mode = True
                if self.camera:
                    try:
                        self.camera.close()
                    except:
                        pass
                    self.camera = None
        else:
            print("[OK] Camera running in simulation mode")
    
    def capture_still(self, filepath):
        """Save a still image to the given path. Returns True on success."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            if self.simulation_mode:
                # Create a placeholder file
                import numpy as np
                try:
                    from PIL import Image
                    # Create a simple test image
                    img_array = np.random.randint(0, 255, 
                                                 (self.config['hardware']['camera']['resolution'][1],
                                                  self.config['hardware']['camera']['resolution'][0], 
                                                  3), 
                                                 dtype=np.uint8)
                    img = Image.fromarray(img_array)
                    img.save(filepath)
                except ImportError:
                    # Just create an empty file
                    with open(filepath, 'w') as f:
                        f.write(f"Simulated image captured at {datetime.now().isoformat()}\n")
                
                print(f"  [SIM] Still image captured: {filepath}")
                return True
            else:
                self.camera.capture_file(filepath)
                print(f"  [OK] Still image captured: {filepath}")
                return True
                
        except Exception as e:
            print(f"  [FAIL] Error capturing still image: {e}")
            return False
    
    def start_video_recording(self, filepath):
        """
        Start video recording
        """
        if self.is_recording:
            print("  ! Video recording already in progress")
            return False
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            if self.simulation_mode:
                # Create a placeholder file
                with open(filepath, 'w') as f:
                    f.write(f"Simulated video recording started at {datetime.now().isoformat()}\n")
                self.current_video_path = filepath
                self.is_recording = True
                print(f"  [SIM] Video recording started: {filepath}")
                return True
            else:
                # Configure for video
                video_config = self.camera.create_video_config(
                    main={"size": tuple(self.config['hardware']['camera']['resolution'])},
                )
                self.camera.configure(video_config)
                
                encoder = H264Encoder(bitrate=10000000)
                self.camera.start_recording(encoder, filepath)
                
                self.current_video_path = filepath
                self.is_recording = True
                print(f"  [OK] Video recording started: {filepath}")
                return True
                
        except Exception as e:
            print(f"  [FAIL] Error starting video recording: {e}")
            self.is_recording = False
            return False
    
    def stop_video_recording(self):
        """
        Stop video recording
        """
        if not self.is_recording:
            print("  ! No video recording in progress")
            return None
        
        try:
            if self.simulation_mode:
                # Append to placeholder file
                with open(self.current_video_path, 'a') as f:
                    f.write(f"Video recording stopped at {datetime.now().isoformat()}\n")
                print(f"  [SIM] Video recording stopped: {self.current_video_path}")
            else:
                self.camera.stop_recording()
                print(f"  [OK] Video recording stopped: {self.current_video_path}")
            
            video_path = self.current_video_path
            self.current_video_path = None
            self.is_recording = False
            
            return video_path
            
        except Exception as e:
            print(f"  [FAIL] Error stopping video recording: {e}")
            self.is_recording = False
            return None
    
    def record_video_clip(self, filepath, duration=None):
        """
        Record a video clip for specified duration
        """
        if duration is None:
            duration = self.config['hardware']['camera'].get('video_duration', 10)
        
        if self.start_video_recording(filepath):
            time.sleep(duration)
            return self.stop_video_recording()
        
        return None
    
    def get_camera_info(self):
        """Get camera information"""
        if self.simulation_mode:
            return {
                'mode': 'simulation',
                'resolution': self.config['hardware']['camera']['resolution'],
                'status': 'active'
            }
        else:
            try:
                return {
                    'mode': 'hardware',
                    'resolution': self.config['hardware']['camera']['resolution'],
                    'status': 'active',
                    'camera_properties': self.camera.camera_properties
                }
            except:
                return {'mode': 'hardware', 'status': 'error'}
    
    def cleanup(self):
        """Cleanup camera resources"""
        if self.is_recording:
            self.stop_video_recording()
        
        if self.camera and not self.simulation_mode:
            try:
                self.camera.stop()
                self.camera.close()
                print("[OK] Camera cleaned up")
            except Exception as e:
                print(f"Error during camera cleanup: {e}")
