"""
Camera Sensor Module for Hardware Mode
Captures still images and videos using rpicam-still and rpicam-vid
Ported from drone_project/field_testing/sensors/camera_sensor.py
"""

import os
import time
import subprocess
import threading
from datetime import datetime
from pathlib import Path

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


class CameraSensor:
    def __init__(self, config, simulation_mode=False):
        """
        Initialize camera sensor
        
        Args:
            config: Configuration dictionary
            simulation_mode: If True, simulate camera
        """
        self.config = config
        self.simulation_mode = simulation_mode or not CAMERA_AVAILABLE
        self.capture_count = 0
        self.video_count = 0
        
        # Get output path from config
        camera_config = config.get('hardware', {}).get('camera', {})
        self.output_path = camera_config.get('output_path', 'data/images')
        self.video_output_path = camera_config.get('video_output_path', 'data/videos')
        
        # Camera lock to prevent simultaneous access
        self.camera_lock = threading.Lock()
        
        # Video configuration
        self.video_enabled = camera_config.get('video_enabled', False)
        
        # Ensure output directories exist
        os.makedirs(self.output_path, exist_ok=True)
        if self.video_enabled:
            os.makedirs(self.video_output_path, exist_ok=True)
        
        if not self.simulation_mode:
            try:
                result = subprocess.run(['rpicam-still', '--version'], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=5)
                if result.returncode == 0:
                    print("[OK] Camera sensor initialized (rpicam-still)")
                else:
                    raise Exception("rpicam-still not responding")
            except Exception as e:
                print(f"[FAIL] Failed to initialize camera: {e}")
                print("  Falling back to simulation mode")
                self.simulation_mode = True
        else:
            print("[OK] Camera sensor in simulation mode")
    
    def capture(self, output_dir=None, filename_prefix="image"):
        """
        Capture a still image
        
        Args:
            output_dir: Output directory (uses self.output_path if None)
            filename_prefix: Prefix for filename
            
        Returns:
            dict with capture info or None on error
        """
        if output_dir is None:
            output_dir = self.output_path
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{self.capture_count:04d}_{timestamp}.jpg"
        filepath = os.path.join(output_dir, filename)
        
        os.makedirs(output_dir, exist_ok=True)
        
        with self.camera_lock:
            return self._capture_internal(filepath, filename)
    
    def _capture_internal(self, filepath, filename):
        """Internal capture method (called with lock held)"""
        try:
            if self.simulation_mode:
                import numpy as np
                try:
                    from PIL import Image
                    camera_config = self.config.get('hardware', {}).get('camera', {})
                    resolution = camera_config.get('resolution', [1920, 1080])
                    quality = camera_config.get('quality', 90)
                    
                    img_array = np.random.randint(0, 255, 
                                                 (resolution[1], resolution[0], 3), 
                                                 dtype=np.uint8)
                    img = Image.fromarray(img_array)
                    img.save(filepath, quality=quality)
                except ImportError:
                    with open(filepath, 'w') as f:
                        f.write(f"Simulated image captured at {datetime.now().isoformat()}\n")
            else:
                camera_config = self.config.get('hardware', {}).get('camera', {})
                width, height = camera_config.get('resolution', [1920, 1080])
                rotation = camera_config.get('rotation', 0)
                quality = camera_config.get('quality', 90)
                
                cmd = [
                    'rpicam-still',
                    '-o', filepath,
                    '--width', str(width),
                    '--height', str(height),
                    '--quality', str(quality),
                    '--nopreview',
                    '--immediate',
                    '--timeout', '1'
                ]
                
                if rotation in [0, 180]:
                    cmd.extend(['--rotation', str(rotation)])
                
                result = subprocess.run(cmd, 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=10)
                
                if result.returncode != 0:
                    raise Exception(f"rpicam-still failed: {result.stderr}")
                
                if rotation in [90, 270]:
                    try:
                        from PIL import Image
                        img = Image.open(filepath)
                        img_rotated = img.rotate(-rotation, expand=True)
                        img_rotated.save(filepath, quality=quality)
                    except ImportError:
                        print(f"  [WARN] PIL not available, cannot rotate {rotation}°")
                    except Exception as e:
                        print(f"  [WARN] Software rotation failed: {e}")
            
            self.capture_count += 1
            
            file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
            
            capture_info = {
                'timestamp': datetime.now().isoformat(),
                'filename': filename,
                'filepath': filepath,
                'capture_number': self.capture_count,
                'file_size_bytes': file_size,
                'mode': 'simulation' if self.simulation_mode else 'hardware'
            }
            
            print(f"  [OK] Image captured: {filename} ({file_size/1024:.1f} KB)")
            return capture_info
            
        except Exception as e:
            print(f"  [FAIL] Error capturing image: {e}")
            return None
    
    def capture_video(self, output_dir=None, filename_prefix="video", duration=5):
        """
        Capture a short video clip
        
        Args:
            output_dir: Output directory (uses self.video_output_path if None)
            filename_prefix: Prefix for filename
            duration: Duration in seconds
            
        Returns:
            dict with capture info or None on error
        """
        if not self.video_enabled:
            return None
        
        if output_dir is None:
            output_dir = self.video_output_path
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{self.video_count:04d}_{timestamp}.h264"
        filepath = os.path.join(output_dir, filename)
        
        os.makedirs(output_dir, exist_ok=True)
        
        with self.camera_lock:
            return self._capture_video_internal(filepath, filename, duration)
    
    def _capture_video_internal(self, filepath, filename, duration):
        """Internal video capture method (called with lock held)"""
        try:
            if self.simulation_mode or not VIDEO_AVAILABLE:
                with open(filepath, 'w') as f:
                    f.write(f"Simulated video captured at {datetime.now().isoformat()}\n")
                    f.write(f"Duration: {duration} seconds\n")
            else:
                camera_config = self.config.get('hardware', {}).get('camera', {})
                video_config = camera_config.get('video', {})
                width, height = video_config.get('resolution', [1920, 1080])
                fps = video_config.get('fps', 30)
                rotation = camera_config.get('rotation', 0)
                codec = video_config.get('codec', 'h264')
                
                cmd = [
                    'rpicam-vid',
                    '-o', filepath,
                    '--width', str(width),
                    '--height', str(height),
                    '--framerate', str(fps),
                    '--timeout', str(duration * 1000),
                    '--nopreview',
                    '--codec', codec
                ]
                
                if rotation in [0, 180]:
                    cmd.extend(['--rotation', str(rotation)])
                
                result = subprocess.run(cmd, 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=duration + 10)
                
                if result.returncode != 0:
                    raise Exception(f"rpicam-vid failed: {result.stderr}")
            
            self.video_count += 1
            
            file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
            
            capture_info = {
                'timestamp': datetime.now().isoformat(),
                'filename': filename,
                'filepath': filepath,
                'capture_number': self.video_count,
                'file_size_bytes': file_size,
                'duration_seconds': duration,
                'mode': 'simulation' if (self.simulation_mode or not VIDEO_AVAILABLE) else 'hardware'
            }
            
            print(f"  [OK] Video captured: {filename} ({file_size/1024:.1f} KB, {duration}s)")
            return capture_info
            
        except Exception as e:
            print(f"  [FAIL] Error capturing video: {e}")
            return None
    
    def get_status(self):
        """Get sensor status"""
        return {
            'sensor': 'Camera',
            'model': 'Arducam IMX708',
            'status': 'active' if not self.simulation_mode else 'simulation',
            'captures': self.capture_count,
            'videos': self.video_count,
            'video_enabled': self.video_enabled
        }
    
    def cleanup(self):
        """Cleanup camera resources"""
        if not self.simulation_mode:
            print("[OK] Camera sensor cleaned up")
