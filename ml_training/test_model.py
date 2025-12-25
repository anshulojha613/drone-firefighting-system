"""
Fire Detection Model Testing Script
Test trained model on individual images or directories
"""

import os
import sys
import argparse
from pathlib import Path

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("[FAIL] OpenCV required. Install: pip install opencv-python")

try:
    import tensorflow as tf
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("[FAIL] TensorFlow required. Install: pip install tensorflow")


class FireModelTester:
    """Test fire detection model on images"""
    
    def __init__(self, model_path, input_size=(224, 224)):
        self.model_path = Path(model_path)
        self.input_size = input_size
        self.model = None
        self.is_tflite = model_path.endswith('.tflite')
        
        self._load_model()
    
    def _load_model(self):
        """Load model from file"""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")
        
        print(f"[LOAD] Loading model: {self.model_path}")
        
        if self.is_tflite:
            self.model = tf.lite.Interpreter(model_path=str(self.model_path))
            self.model.allocate_tensors()
            self.input_details = self.model.get_input_details()
            self.output_details = self.model.get_output_details()
            print("[OK] TFLite model loaded")
        else:
            self.model = tf.keras.models.load_model(str(self.model_path))
            print("[OK] Keras model loaded")
    
    def get_model_info(self):
        """Get model information and statistics"""
        info = {
            'model_path': str(self.model_path),
            'model_type': 'TFLite' if self.is_tflite else 'Keras',
            'input_size': self.input_size,
            'file_size_mb': self.model_path.stat().st_size / (1024 * 1024)
        }
        
        if self.is_tflite:
            info['input_shape'] = self.input_details[0]['shape'].tolist()
            info['input_dtype'] = str(self.input_details[0]['dtype'])
            info['output_shape'] = self.output_details[0]['shape'].tolist()
        else:
            info['total_params'] = self.model.count_params()
            info['trainable_params'] = sum(
                tf.keras.backend.count_params(w) for w in self.model.trainable_weights
            )
        
        return info
    
    def print_model_info(self):
        """Print model information"""
        info = self.get_model_info()
        
        print("\n" + "="*60)
        print("[INFO] MODEL DETAILS")
        print("="*60)
        print(f"   Path: {info['model_path']}")
        print(f"   Type: {info['model_type']}")
        print(f"   File Size: {info['file_size_mb']:.2f} MB")
        print(f"   Input Size: {info['input_size'][0]}x{info['input_size'][1]}")
        
        if self.is_tflite:
            print(f"   Input Shape: {info['input_shape']}")
            print(f"   Input Dtype: {info['input_dtype']}")
            print(f"   Output Shape: {info['output_shape']}")
        else:
            print(f"   Total Params: {info['total_params']:,}")
            print(f"   Trainable Params: {info['trainable_params']:,}")
        
        # Show all model files in models directory
        models_dir = Path('models')
        if models_dir.exists():
            print("\n[FILES] Available models:")
            for f in sorted(models_dir.glob('fire_detector*')):
                size_mb = f.stat().st_size / (1024 * 1024)
                print(f"   {f.name}: {size_mb:.2f} MB")
    
    def predict(self, image_path):
        """
        Predict if image contains fire
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            return {'error': f"Image not found: {image_path}"}
        
        # Load image using Keras (same as training)
        try:
            img = tf.keras.utils.load_img(str(image_path), target_size=self.input_size)
            img_array = tf.keras.utils.img_to_array(img)
            input_data = np.expand_dims(img_array, axis=0)
        except Exception as e:
            return {'error': f"Could not read image: {image_path} - {e}"}
        
        if self.is_tflite:
            # TFLite inference
            self.model.set_tensor(self.input_details[0]['index'], input_data)
            self.model.invoke()
            
            output_data = self.model.get_tensor(self.output_details[0]['index'])
            confidence = float(output_data[0][0])
        else:
            # Keras inference
            
            prediction = self.model.predict(input_data, verbose=0)
            confidence = float(prediction[0][0])
        
        # Model outputs probability for class 1 (alphabetically second folder)
        # fire_images=0, non_fire_images=1, so confidence > 0.5 means NO FIRE
        fire_detected = confidence < 0.5
        fire_confidence = 1.0 - confidence  # Show fire probability (class 0)
        
        return {
            'fire_detected': fire_detected,
            'confidence': fire_confidence,
            'image_path': str(image_path),
            'label': 'FIRE' if fire_detected else 'NO FIRE'
        }
    
    def test_directory(self, directory, expected_label=None):
        """
        Test all images in a directory
        """
        dir_path = Path(directory)
        
        if not dir_path.exists():
            return {'error': f"Directory not found: {dir_path}"}
        
        images = list(dir_path.glob('*.jpg')) + list(dir_path.glob('*.png'))
        images += list(dir_path.glob('*.jpeg'))
        
        if not images:
            return {'error': f"No images found in: {dir_path}"}
        
        print(f"\n[TEST] Testing {len(images)} images from: {dir_path}")
        
        results = []
        correct = 0
        
        for img_path in images:
            result = self.predict(img_path)
            results.append(result)
            
            if 'error' not in result:
                status = "[FIRE]" if result['fire_detected'] else "[----]"
                print(f"   {status} {result['confidence']:.3f} - {img_path.name}")
                
                if expected_label:
                    expected_fire = expected_label == 'fire'
                    if result['fire_detected'] == expected_fire:
                        correct += 1
        
        summary = {
            'total': len(images),
            'fire_detected': sum(1 for r in results if r.get('fire_detected')),
            'no_fire_detected': sum(1 for r in results if not r.get('fire_detected') and 'error' not in r),
            'errors': sum(1 for r in results if 'error' in r),
            'results': results
        }
        
        if expected_label:
            accuracy = correct / len(images) if images else 0
            summary['accuracy'] = accuracy
            summary['correct'] = correct
            print(f"\n   Accuracy: {accuracy:.1%} ({correct}/{len(images)})")
        
        return summary
    
    def benchmark(self, image_path, iterations=100):
        """Benchmark inference speed"""
        import time
        
        print(f"\n[BENCH] Running {iterations} iterations...")
        
        # Warm up
        for _ in range(5):
            self.predict(image_path)
        
        # Benchmark
        start = time.time()
        for _ in range(iterations):
            self.predict(image_path)
        elapsed = time.time() - start
        
        avg_ms = (elapsed / iterations) * 1000
        fps = iterations / elapsed
        
        print(f"   Average: {avg_ms:.2f} ms per image")
        print(f"   Throughput: {fps:.1f} FPS")
        
        return {'avg_ms': avg_ms, 'fps': fps}


def main():
    parser = argparse.ArgumentParser(description='Test fire detection model')
    parser.add_argument('--model', type=str, default='models/fire_detector.tflite',
                        help='Path to model file (.tflite or .keras)')
    parser.add_argument('--image', type=str,
                        help='Test single image')
    parser.add_argument('--dir', type=str,
                        help='Test all images in directory')
    parser.add_argument('--fire-dir', type=str,
                        help='Test fire images directory (for accuracy)')
    parser.add_argument('--no-fire-dir', type=str,
                        help='Test no-fire images directory (for accuracy)')
    parser.add_argument('--benchmark', type=str,
                        help='Benchmark inference speed on image')
    parser.add_argument('--iterations', type=int, default=100,
                        help='Benchmark iterations')
    parser.add_argument('--info', action='store_true',
                        help='Show model information and stats')
    args = parser.parse_args()
    
    if not TF_AVAILABLE or not CV2_AVAILABLE:
        print("[FAIL] Required dependencies not installed")
        return 1
    
    print("="*60)
    print("[ML] FIRE DETECTION MODEL TESTING")
    print("="*60)
    
    try:
        tester = FireModelTester(args.model)
        
        if args.info:
            tester.print_model_info()
        
        if args.image:
            result = tester.predict(args.image)
            if 'error' in result:
                print(f"[FAIL] {result['error']}")
            else:
                print(f"\n[RESULT] {result['label']}")
                print(f"   Confidence: {result['confidence']:.3f}")
                print(f"   Image: {result['image_path']}")
        
        if args.dir:
            tester.test_directory(args.dir)
        
        if args.fire_dir:
            print("\n[TEST] Fire images:")
            tester.test_directory(args.fire_dir, expected_label='fire')
        
        if args.no_fire_dir:
            print("\n[TEST] No-fire images:")
            tester.test_directory(args.no_fire_dir, expected_label='no_fire')
        
        if args.benchmark:
            tester.benchmark(args.benchmark, iterations=args.iterations)
        
        return 0
        
    except FileNotFoundError as e:
        print(f"[FAIL] {e}")
        return 1
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
