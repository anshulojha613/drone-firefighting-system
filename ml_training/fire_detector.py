"""
Fire Detection ML Module
Simple thermal-based fire detection for SD drones
"""
import numpy as np
from typing import Dict, Tuple


class FireDetector:
    def __init__(self, hotspot_threshold_c: float = 50.0, min_pixels: int = 3):
        self.hotspot_threshold = hotspot_threshold_c
        self.min_pixels = min_pixels
    
    def detect_fire(self, thermal_frame: np.ndarray, gps_data: Dict) -> Tuple[bool, Dict]:
        """
        Detect fire from thermal frame
        """
        # Find hotspot pixels
        hotspot_mask = thermal_frame >= self.hotspot_threshold
        hotspot_count = np.sum(hotspot_mask)
        
        if hotspot_count >= self.min_pixels:
            # Fire detected
            max_temp = np.max(thermal_frame)
            mean_temp = np.mean(thermal_frame[hotspot_mask])
            
            # Find hotspot center
            hotspot_coords = np.argwhere(hotspot_mask)
            center_y, center_x = hotspot_coords.mean(axis=0)
            
            detection_info = {
                'detected': True,
                'latitude': gps_data['latitude'],
                'longitude': gps_data['longitude'],
                'altitude': gps_data['altitude'],
                'max_temperature_c': float(max_temp),
                'mean_temperature_c': float(mean_temp),
                'hotspot_pixels': int(hotspot_count),
                'confidence': min(0.95, 0.5 + (max_temp - self.hotspot_threshold) / 100),
                'detection_method': 'thermal',
                'center_pixel': (int(center_y), int(center_x))
            }
            
            return True, detection_info
        
        return False, {'detected': False}
    
    def analyze_thermal_dataset(self, thermal_frames: list, gps_data: list) -> list:
        """
        Analyze complete thermal dataset for fires
        """
        detections = []
        
        for i, frame in enumerate(thermal_frames):
            if i < len(gps_data):
                is_fire, info = self.detect_fire(frame['data'], gps_data[i])
                
                if is_fire:
                    info['timestamp'] = frame['timestamp']
                    info['frame_number'] = frame['frame_number']
                    detections.append(info)
        
        return detections
