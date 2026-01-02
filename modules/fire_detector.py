"""
Fire Detection Module
Uses image recognition to confirm fire/smoke detection
"""

import os
import cv2
import numpy as np
from datetime import datetime

try:
    import tensorflow as tf
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    # Note: TensorFlow is optional. Basic fire detection uses thermal thresholding.


class FireDetector:
    """Detects fire/smoke in images using ML model or color-based analysis."""
    
    def __init__(self, config, simulation_mode=False):
        self.config = config
        self.simulation_mode = simulation_mode or not TF_AVAILABLE
        self.model = None
        self.input_size = tuple(config['fire_detection']['image_recognition']['input_size'])
        self.confidence_threshold = config['fire_detection']['image_recognition']['confidence_threshold']
        
        # For simulation mode
        self.sim_objects = config['fire_detection']['image_recognition'].get('simulation_objects', 
                                                                              ['fire', 'smoke'])
        
        if not self.simulation_mode:
            model_path = config['fire_detection']['image_recognition'].get('model_path')
            if model_path and os.path.exists(model_path):
                try:
                    self.model = tf.lite.Interpreter(model_path=model_path)
                    self.model.allocate_tensors()
                    print("[OK] Fire detection model loaded")
                except Exception as e:
                    print(f"[FAIL] Failed to load model: {e}")
                    print("  Using color-based detection")
                    self.simulation_mode = True
            else:
                print("[OK] Fire detector using color-based detection (no model provided)")
                self.simulation_mode = True
        else:
            print("[OK] Fire detector running in simulation mode")
    
    def detect_fire_in_image(self, image_path):
        """Analyze image for fire/smoke. Returns dict with 'detected', 'confidence', 'method'."""
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                print(f"  [FAIL] Could not load image: {image_path}")
                return None
            
            if self.simulation_mode or self.model is None:
                # Use color-based detection as fallback
                return self._detect_fire_color_based(image)
            else:
                # Use ML model
                return self._detect_fire_ml(image)
                
        except Exception as e:
            print(f"  [FAIL] Error detecting fire in image: {e}")
            return None
    
    def _detect_fire_color_based(self, image):
        """
        Simple color-based fire detection
        Detects red/orange/yellow colors typical of fire
        """
        # Convert to HSV color space
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Define color ranges for fire (red, orange, yellow)
        # Red range 1 (wraps around in HSV)
        lower_red1 = np.array([0, 50, 50])
        upper_red1 = np.array([10, 255, 255])
        
        # Red range 2
        lower_red2 = np.array([170, 50, 50])
        upper_red2 = np.array([180, 255, 255])
        
        # Orange/Yellow range
        lower_orange = np.array([10, 50, 50])
        upper_orange = np.array([30, 255, 255])
        
        # Create masks
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask3 = cv2.inRange(hsv, lower_orange, upper_orange)
        
        # Combine masks
        fire_mask = mask1 | mask2 | mask3
        
        # Calculate percentage of fire-colored pixels
        fire_pixels = np.sum(fire_mask > 0)
        total_pixels = fire_mask.shape[0] * fire_mask.shape[1]
        fire_percentage = (fire_pixels / total_pixels) * 100
        
        # Determine if fire is detected
        detected = fire_percentage > 1.0  # At least 1% fire-colored pixels
        confidence = min(fire_percentage / 10.0, 1.0)  # Scale to 0-1
        
        result = {
            'detected': detected,
            'confidence': float(confidence),
            'method': 'color_based',
            'fire_percentage': float(fire_percentage),
            'fire_pixels': int(fire_pixels),
            'timestamp': datetime.now().isoformat()
        }
        
        if detected:
            print(f"  [FIRE] Fire detected! Confidence: {confidence:.2f}, "
                  f"Fire pixels: {fire_percentage:.1f}%")
        
        return result
    
    def _detect_fire_ml(self, image):
        """
        ML-based fire detection using TensorFlow Lite model
        """
        try:
            # Preprocess image
            input_details = self.model.get_input_details()
            output_details = self.model.get_output_details()
            
            # Resize image to model input size
            image_resized = cv2.resize(image, self.input_size)
            image_rgb = cv2.cvtColor(image_resized, cv2.COLOR_BGR2RGB)
            
            # Normalize
            input_data = np.expand_dims(image_rgb, axis=0).astype(np.float32)
            input_data = input_data / 255.0
            
            # Run inference
            self.model.set_tensor(input_details[0]['index'], input_data)
            self.model.invoke()
            
            # Get output
            output_data = self.model.get_tensor(output_details[0]['index'])
            confidence = float(output_data[0][0])
            
            detected = confidence > self.confidence_threshold
            
            result = {
                'detected': detected,
                'confidence': confidence,
                'method': 'ml_model',
                'timestamp': datetime.now().isoformat()
            }
            
            if detected:
                print(f"  [FIRE] Fire detected! Confidence: {confidence:.2f}")
            
            return result
            
        except Exception as e:
            print(f"  [FAIL] Error in ML detection: {e}")
            # Fallback to color-based
            return self._detect_fire_color_based(image)
    
    def detect_objects_in_image(self, image_path, target_objects=None):
        """
        Detect specific objects in image (for simulation)
        """
        if target_objects is None:
            target_objects = self.sim_objects
        
        # For simulation, we'll use a simple approach
        # In real buildation, you'd use object detection model like YOLO or MobileNet
        
        try:
            image = cv2.imread(image_path)
            if image is None:
                return {'detected': False, 'objects': [], 'method': 'simulation'}
            
            # Use color-based detection as proxy
            fire_result = self._detect_fire_color_based(image)
            
            detected_objects = []
            if fire_result['detected']:
                # Simulate object detection
                detected_objects.append({
                    'object': 'fire',
                    'confidence': fire_result['confidence']
                })
            
            result = {
                'detected': len(detected_objects) > 0,
                'objects': detected_objects,
                'method': 'simulation',
                'timestamp': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            print(f"  [FAIL] Error detecting objects: {e}")
            return {'detected': False, 'objects': [], 'method': 'error'}
    
    def validate_fire_detection(self, thermal_result, image_path):
        """
        Validate fire detection using both thermal and visual data
        """
        if not thermal_result or not thermal_result.get('detected'):
            return {
                'validated': False,
                'reason': 'no_thermal_hotspot',
                'timestamp': datetime.now().isoformat()
            }
        
        # Check visual confirmation
        visual_result = self.detect_fire_in_image(image_path)
        
        if not visual_result:
            return {
                'validated': False,
                'reason': 'visual_detection_failed',
                'thermal_result': thermal_result,
                'timestamp': datetime.now().isoformat()
            }
        
        # Combine results
        validated = visual_result.get('detected', False)
        
        result = {
            'validated': validated,
            'thermal_result': thermal_result,
            'visual_result': visual_result,
            'combined_confidence': (thermal_result.get('max_temperature', 0) / 100.0 + 
                                   visual_result.get('confidence', 0)) / 2.0,
            'timestamp': datetime.now().isoformat()
        }
        
        if validated:
            print("  [OK] Fire detection VALIDATED by visual confirmation")
        else:
            print("  [FAIL] Fire detection NOT validated by visual confirmation")
        
        return result
