"""
Thermal Sensor Module for Hardware Mode
Captures thermal images using MLX90640 sensor
Ported from drone_project/field_testing/sensors/thermal_sensor.py
"""

import os
import time
import numpy as np
import csv
from datetime import datetime
from pathlib import Path

try:
    import board
    import busio
    import adafruit_mlx90640
    THERMAL_AVAILABLE = True
except ImportError:
    THERMAL_AVAILABLE = False


class ThermalSensor:
    def __init__(self, config, simulation_mode=False):
        """
        Initialize thermal sensor
        
        Args:
            config: Configuration dictionary
            simulation_mode: If True, simulate thermal camera
        """
        self.config = config
        self.simulation_mode = simulation_mode or not THERMAL_AVAILABLE
        self.mlx = None
        self.frame = np.zeros((24, 32))
        self.capture_count = 0
        
        # Get output path from config
        thermal_config = config.get('hardware', {}).get('thermal', {})
        self.output_path = thermal_config.get('output_path', 'data/thermal')
        self.save_format = thermal_config.get('save_format', 'both')
        
        os.makedirs(self.output_path, exist_ok=True)
        
        if not self.simulation_mode:
            try:
                i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)
                self.mlx = adafruit_mlx90640.MLX90640(i2c)
                self.mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ
                print("[OK] Thermal sensor initialized (MLX90640)")
            except Exception as e:
                print(f"[FAIL] Failed to initialize thermal sensor: {e}")
                print("  Falling back to simulation mode")
                self.simulation_mode = True
        else:
            print("[OK] Thermal sensor in simulation mode")
    
    def capture(self, output_dir=None, filename_prefix="thermal"):
        """
        Capture thermal frame
        
        Args:
            output_dir: Output directory (uses self.output_path if None)
            filename_prefix: Prefix for filename
            
        Returns:
            dict with capture info or None on error
        """
        if output_dir is None:
            output_dir = self.output_path
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{filename_prefix}_{self.capture_count:04d}_{timestamp}"
        
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            if self.simulation_mode:
                self.frame = np.random.normal(25, 3, (24, 32))
                if np.random.random() < 0.1:
                    x, y = np.random.randint(8, 16), np.random.randint(8, 24)
                    self.frame[x-2:x+2, y-2:y+2] = np.random.uniform(40, 60)
            else:
                frame_data = [0] * 768
                self.mlx.getFrame(frame_data)
                self.frame = np.array(frame_data).reshape((24, 32))
            
            stats = {
                'min_temp': float(np.min(self.frame)),
                'max_temp': float(np.max(self.frame)),
                'mean_temp': float(np.mean(self.frame)),
                'std_temp': float(np.std(self.frame))
            }
            
            files_saved = []
            
            if self.save_format in ['npy', 'both']:
                npy_path = os.path.join(output_dir, f"{base_filename}.npy")
                np.save(npy_path, self.frame)
                files_saved.append(npy_path)
            
            if self.save_format in ['csv', 'both']:
                csv_path = os.path.join(output_dir, f"{base_filename}.csv")
                with open(csv_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['# Thermal Frame Data'])
                    writer.writerow(['# Timestamp:', datetime.now().isoformat()])
                    writer.writerow(['# Min Temp:', f"{stats['min_temp']:.2f}"])
                    writer.writerow(['# Max Temp:', f"{stats['max_temp']:.2f}"])
                    writer.writerow(['# Mean Temp:', f"{stats['mean_temp']:.2f}"])
                    writer.writerow(['# Resolution: 24x32'])
                    writer.writerow([])
                    for row in self.frame:
                        writer.writerow([f"{temp:.2f}" for temp in row])
                files_saved.append(csv_path)
            
            self.capture_count += 1
            
            capture_info = {
                'timestamp': datetime.now().isoformat(),
                'base_filename': base_filename,
                'files': files_saved,
                'capture_number': self.capture_count,
                'statistics': stats,
                'resolution': [24, 32],
                'frame_data': self.frame,
                'mode': 'simulation' if self.simulation_mode else 'hardware'
            }
            
            print(f"  [OK] Thermal captured: {base_filename} "
                  f"(Min: {stats['min_temp']:.1f}°C, Max: {stats['max_temp']:.1f}°C, "
                  f"Mean: {stats['mean_temp']:.1f}°C)")
            
            return capture_info
            
        except Exception as e:
            print(f"  [FAIL] Error capturing thermal frame: {e}")
            return None
    
    def get_status(self):
        """Get sensor status"""
        return {
            'sensor': 'Thermal Camera',
            'model': 'MLX90640',
            'status': 'active' if not self.simulation_mode else 'simulation',
            'captures': self.capture_count,
            'resolution': '32x24'
        }
    
    def cleanup(self):
        """Cleanup thermal sensor resources"""
        if self.mlx:
            try:
                print("[OK] Thermal sensor cleaned up")
            except Exception as e:
                print(f"Error during thermal sensor cleanup: {e}")
