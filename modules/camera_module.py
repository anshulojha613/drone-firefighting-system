"""
Camera Module - Arducam IMX708
Handles still image and video capture
"""

import time
import os
import subprocess
from datetime import datetime
from pathlib import Path

# Check if rpicam tools are available (Raspberry Pi command-line tools)
def check_rpicam_available():
    try:
        result = subprocess.run(['which', 'rpicam-still'], 
                              capture_output=True, 
                              text=True, 
                              timeout=2)
        return result.returncode == 0
    except:
        return False

def check_rpicam_vid_available():
    try:
        result = subprocess.run(['which', 'rpicam-vid'], 
                              capture_output=True, 
                              text=True, 
                              timeout=2)
        return result.returncode == 0
    except:
        return False

CAMERA_AVAILABLE = check_rpicam_available()
VIDEO_AVAILABLE = check_rpicam_vid_available()
if not CAMERA_AVAILABLE:
    print("Warning: rpicam-still not available. Running in simulation mode.")
if not VIDEO_AVAILABLE:
    print("Warning: rpicam-vid not available. Video recording will be simulated.")


class CameraModule:
    """Handles still image and video capture from Arducam IMX708 or simulation."""
    
    def __init__(self, config, simulation_mode=False):
        self.config = config
        self.simulation_mode = simulation_mode or not CAMERA_AVAILABLE
        self.is_recording = False
        self.current_video_path = None
        self.capture_count = 0
        
        if not self.simulation_mode:
            try:
                # Test rpicam-still with a quick command
                result = subprocess.run(['rpicam-still', '--version'], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=5)
                if result.returncode == 0:
                    print("[OK] Camera initialized (rpicam-still)")
                else:
                    raise Exception("rpicam-still not responding")
            except Exception as e:
                print(f"[FAIL] Failed to initialize camera: {e}")
                print("  Falling back to simulation mode")
                self.simulation_mode = True
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
                # Use rpicam-still command
                resolution = self.config['hardware']['camera']['resolution']
                rotation = self.config['hardware']['camera'].get('rotation', 0)
                quality = self.config['hardware']['camera'].get('quality', 90)
                
                cmd = [
                    'rpicam-still',
                    '-o', filepath,
                    '--width', str(resolution[0]),
                    '--height', str(resolution[1]),
                    '--rotation', str(rotation),
                    '--quality', str(quality),
                    '-n',  # No preview
                    '-t', '1'  # 1ms timeout (immediate capture)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    self.capture_count += 1
                    print(f"  [OK] Still image captured: {filepath}")
                    return True
                else:
                    print(f"  [FAIL] rpicam-still error: {result.stderr}")
                    return False
                
        except Exception as e:
            print(f"  [FAIL] Error capturing still image: {e}")
            return False
    
    def start_video_recording(self, filepath, duration=10):
        """
        Start video recording (uses rpicam-vid with duration)
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
                if not VIDEO_AVAILABLE:
                    print("  [FAIL] rpicam-vid not available")
                    return False
                
                # Use rpicam-vid command
                resolution = self.config['hardware']['camera']['resolution']
                rotation = self.config['hardware']['camera'].get('rotation', 0)
                
                cmd = [
                    'rpicam-vid',
                    '-o', filepath,
                    '--width', str(resolution[0]),
                    '--height', str(resolution[1]),
                    '--rotation', str(rotation),
                    '-n',  # No preview
                    '-t', str(duration * 1000)  # Duration in milliseconds
                ]
                
                # Run in background
                self.video_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
                # Wait for rpicam-vid process to complete
                if hasattr(self, 'video_process'):
                    self.video_process.wait(timeout=30)
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
                    'tool': 'rpicam-still'
                }
            except:
                return {'mode': 'hardware', 'status': 'error'}
    
    def cleanup(self):
        """Cleanup camera resources"""
        if self.is_recording:
            self.stop_video_recording()
        
        if not self.simulation_mode:
            try:
                # Terminate any running video process
                if hasattr(self, 'video_process') and self.video_process:
                    self.video_process.terminate()
                    self.video_process.wait(timeout=5)
                print("[OK] Camera cleaned up")
            except Exception as e:
                print(f"Error during camera cleanup: {e}")
