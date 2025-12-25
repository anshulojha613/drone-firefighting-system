"""
Fire Detection Model Training Script
Trains a CNN to classify images as fire/no-fire
Exports to TensorFlow Lite for deployment on Raspberry Pi
"""

import os
import sys
import argparse
import numpy as np
from pathlib import Path

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("[FAIL] TensorFlow not installed. Install with: pip install tensorflow")
    sys.exit(1)


class FireModelTrainer:
    """Trains fire detection CNN model"""
    
    def __init__(self, data_dir, model_dir='models', input_size=(224, 224)):
        self.data_dir = Path(data_dir)
        self.model_dir = Path(model_dir)
        self.input_size = input_size
        self.model = None
        self.history = None
        
        self.model_dir.mkdir(parents=True, exist_ok=True)
    
    def prepare_dataset(self, validation_split=0.2, batch_size=32):
        """
        Load and prepare dataset from directory structure:
        data_dir/
            fire/
                img1.jpg
                img2.jpg
            no_fire/
                img1.jpg
                img2.jpg
        """
        print("\n[DATA] Preparing dataset...")
        print(f"   Source: {self.data_dir}")
        
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")
        
        # Check for required subdirectories (support multiple naming conventions)
        fire_dir = None
        no_fire_dir = None
        
        for fire_name in ['fire', 'fire_images']:
            if (self.data_dir / fire_name).exists():
                fire_dir = self.data_dir / fire_name
                break
        
        for no_fire_name in ['no_fire', 'non_fire_images', 'non_fire']:
            if (self.data_dir / no_fire_name).exists():
                no_fire_dir = self.data_dir / no_fire_name
                break
        
        if fire_dir is None or no_fire_dir is None:
            print(f"\n[FAIL] Expected directory structure:")
            print(f"   {self.data_dir}/")
            print(f"       fire/ or fire_images/")
            print(f"       no_fire/ or non_fire_images/")
            raise FileNotFoundError("Missing fire or no_fire subdirectories")
        
        print(f"   Fire dir: {fire_dir.name}")
        print(f"   No-fire dir: {no_fire_dir.name}")
        
        # Count images
        fire_count = len(list(fire_dir.glob('*.jpg'))) + len(list(fire_dir.glob('*.png')))
        no_fire_count = len(list(no_fire_dir.glob('*.jpg'))) + len(list(no_fire_dir.glob('*.png')))
        
        print(f"   Fire images: {fire_count}")
        print(f"   No-fire images: {no_fire_count}")
        print(f"   Total: {fire_count + no_fire_count}")
        
        if fire_count == 0 or no_fire_count == 0:
            raise ValueError("Need at least one image in each category")
        
        # Create training dataset
        self.train_ds = keras.utils.image_dataset_from_directory(
            self.data_dir,
            validation_split=validation_split,
            subset='training',
            seed=42,
            image_size=self.input_size,
            batch_size=batch_size,
            label_mode='binary'
        )
        
        # Create validation dataset
        self.val_ds = keras.utils.image_dataset_from_directory(
            self.data_dir,
            validation_split=validation_split,
            subset='validation',
            seed=42,
            image_size=self.input_size,
            batch_size=batch_size,
            label_mode='binary'
        )
        
        # Get class names
        self.class_names = self.train_ds.class_names
        print(f"   Classes: {self.class_names}")
        
        # Configure for performance
        AUTOTUNE = tf.data.AUTOTUNE
        self.train_ds = self.train_ds.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)
        self.val_ds = self.val_ds.cache().prefetch(buffer_size=AUTOTUNE)
        
        print("[OK] Dataset prepared")
        return self.train_ds, self.val_ds
    
    def build_model(self, use_transfer_learning=True):
        """
        Build CNN model for fire detection
        """
        print("\n[MODEL] Building model...")
        
        # Data augmentation layer
        data_augmentation = keras.Sequential([
            layers.RandomFlip('horizontal'),
            layers.RandomRotation(0.2),
            layers.RandomZoom(0.2),
            layers.RandomContrast(0.2),
        ])
        
        # Normalization
        preprocess_input = keras.applications.mobilenet_v2.preprocess_input
        
        if use_transfer_learning:
            # Use MobileNetV2 as base (efficient for Raspberry Pi)
            print("   Using MobileNetV2 transfer learning")
            
            base_model = keras.applications.MobileNetV2(
                input_shape=(*self.input_size, 3),
                include_top=False,
                weights='imagenet'
            )
            base_model.trainable = False  # Freeze base model
            
            # Build model
            inputs = keras.Input(shape=(*self.input_size, 3))
            x = data_augmentation(inputs)
            x = preprocess_input(x)
            x = base_model(x, training=False)
            x = layers.GlobalAveragePooling2D()(x)
            x = layers.Dropout(0.3)(x)
            x = layers.Dense(128, activation='relu')(x)
            x = layers.Dropout(0.3)(x)
            outputs = layers.Dense(1, activation='sigmoid')(x)
            
            self.model = keras.Model(inputs, outputs)
            
        else:
            # Simple CNN (smaller, faster training)
            print("   Using simple CNN architecture")
            
            self.model = keras.Sequential([
                layers.Input(shape=(*self.input_size, 3)),
                data_augmentation,
                layers.Rescaling(1./255),
                
                layers.Conv2D(32, 3, activation='relu'),
                layers.MaxPooling2D(),
                layers.Conv2D(64, 3, activation='relu'),
                layers.MaxPooling2D(),
                layers.Conv2D(128, 3, activation='relu'),
                layers.MaxPooling2D(),
                layers.Conv2D(128, 3, activation='relu'),
                layers.MaxPooling2D(),
                
                layers.Flatten(),
                layers.Dropout(0.5),
                layers.Dense(256, activation='relu'),
                layers.Dropout(0.5),
                layers.Dense(1, activation='sigmoid')
            ])
        
        # Compile model - use lower learning rate for transfer learning
        lr = 0.0001 if use_transfer_learning else 0.001
        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=lr),
            loss='binary_crossentropy',
            metrics=['accuracy', keras.metrics.Precision(), keras.metrics.Recall()]
        )
        print(f"   Learning rate: {lr}")
        
        self.model.summary()
        print("[OK] Model built")
        return self.model
    
    def train(self, epochs=20, early_stopping_patience=5):
        """Train the model"""
        print(f"\n[TRAIN] Training for {epochs} epochs...")
        
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")
        
        if not hasattr(self, 'train_ds'):
            raise ValueError("Dataset not prepared. Call prepare_dataset() first.")
        
        # Callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=early_stopping_patience,
                restore_best_weights=True
            ),
            keras.callbacks.ModelCheckpoint(
                filepath=str(self.model_dir / 'fire_model_checkpoint.keras'),
                monitor='val_accuracy',
                save_best_only=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=3,
                min_lr=1e-6
            )
        ]
        
        # Train
        self.history = self.model.fit(
            self.train_ds,
            validation_data=self.val_ds,
            epochs=epochs,
            callbacks=callbacks
        )
        
        # Print final metrics
        final_acc = self.history.history['accuracy'][-1]
        final_val_acc = self.history.history['val_accuracy'][-1]
        print(f"\n[OK] Training complete")
        print(f"   Final accuracy: {final_acc:.4f}")
        print(f"   Final val_accuracy: {final_val_acc:.4f}")
        
        return self.history
    
    def fine_tune(self, epochs=10, unfreeze_layers=50):
        """Fine-tune the model by unfreezing some base layers"""
        print(f"\n[FINE-TUNE] Fine-tuning last {unfreeze_layers} layers...")
        
        # Find base model
        base_model = None
        for layer in self.model.layers:
            if isinstance(layer, keras.Model):
                base_model = layer
                break
        
        if base_model is None:
            print("[SKIP] No base model found for fine-tuning")
            return
        
        # Unfreeze top layers
        base_model.trainable = True
        for layer in base_model.layers[:-unfreeze_layers]:
            layer.trainable = False
        
        # Recompile with lower learning rate
        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=1e-5),
            loss='binary_crossentropy',
            metrics=['accuracy', keras.metrics.Precision(), keras.metrics.Recall()]
        )
        
        # Continue training
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=3,
                restore_best_weights=True
            )
        ]
        
        self.history = self.model.fit(
            self.train_ds,
            validation_data=self.val_ds,
            epochs=epochs,
            callbacks=callbacks
        )
        
        print("[OK] Fine-tuning complete")
        return self.history
    
    def evaluate(self):
        """Evaluate model on validation set"""
        print("\n[EVAL] Evaluating model...")
        
        results = self.model.evaluate(self.val_ds)
        
        print(f"   Loss: {results[0]:.4f}")
        print(f"   Accuracy: {results[1]:.4f}")
        print(f"   Precision: {results[2]:.4f}")
        print(f"   Recall: {results[3]:.4f}")
        
        return results
    
    def save_model(self, name='fire_detector'):
        """Save model in multiple formats"""
        print("\n[SAVE] Saving model...")
        
        # Save Keras model
        keras_path = self.model_dir / f'{name}.keras'
        self.model.save(keras_path)
        print(f"   [OK] Keras model: {keras_path}")
        
        # Save TFLite model (for Raspberry Pi deployment)
        tflite_path = self.model_dir / f'{name}.tflite'
        self._convert_to_tflite(tflite_path)
        print(f"   [OK] TFLite model: {tflite_path}")
        
        # Save quantized TFLite (smaller, faster on Pi)
        tflite_quant_path = self.model_dir / f'{name}_quantized.tflite'
        self._convert_to_tflite(tflite_quant_path, quantize=True)
        print(f"   [OK] Quantized TFLite: {tflite_quant_path}")
        
        print(f"\n[OK] Models saved to: {self.model_dir}")
        return keras_path, tflite_path
    
    def _convert_to_tflite(self, output_path, quantize=False):
        """Convert model to TensorFlow Lite format"""
        converter = tf.lite.TFLiteConverter.from_keras_model(self.model)
        
        if quantize:
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            converter.target_spec.supported_types = [tf.float16]
        
        tflite_model = converter.convert()
        
        with open(output_path, 'wb') as f:
            f.write(tflite_model)
        
        # Print size
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"      Size: {size_mb:.2f} MB")


def create_sample_dataset(output_dir):
    """Create a sample dataset structure with placeholder images"""
    import cv2
    
    output_path = Path(output_dir)
    fire_dir = output_path / 'fire'
    no_fire_dir = output_path / 'no_fire'
    
    fire_dir.mkdir(parents=True, exist_ok=True)
    no_fire_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n[SAMPLE] Creating sample dataset at: {output_path}")
    
    # Create sample fire images (red/orange)
    for i in range(10):
        img = np.zeros((224, 224, 3), dtype=np.uint8)
        # Add fire-like colors
        img[50:150, 50:150] = [0, 100, 255]  # Orange in BGR
        img[70:130, 70:130] = [0, 0, 255]    # Red center
        # Add noise
        noise = np.random.randint(0, 50, (224, 224, 3), dtype=np.uint8)
        img = cv2.add(img, noise)
        cv2.imwrite(str(fire_dir / f'fire_{i:04d}.jpg'), img)
    
    # Create sample no-fire images (green/brown)
    for i in range(10):
        img = np.zeros((224, 224, 3), dtype=np.uint8)
        # Add nature-like colors
        img[:, :] = [34, 139, 34]  # Forest green in BGR
        # Add noise
        noise = np.random.randint(0, 50, (224, 224, 3), dtype=np.uint8)
        img = cv2.add(img, noise)
        cv2.imwrite(str(no_fire_dir / f'no_fire_{i:04d}.jpg'), img)
    
    print(f"   [OK] Created 10 fire images")
    print(f"   [OK] Created 10 no-fire images")
    print(f"\n[TIP] Replace these with real images for production training")
    
    return output_path


def main():
    parser = argparse.ArgumentParser(description='Train fire detection model')
    parser.add_argument('--data-dir', type=str, default='data/training_images',
                        help='Directory containing fire/ and no_fire/ subdirs')
    parser.add_argument('--model-dir', type=str, default='models',
                        help='Directory to save trained models')
    parser.add_argument('--epochs', type=int, default=20,
                        help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=32,
                        help='Training batch size')
    parser.add_argument('--no-transfer', action='store_true',
                        help='Use simple CNN instead of transfer learning')
    parser.add_argument('--fine-tune', action='store_true',
                        help='Fine-tune base model after initial training')
    parser.add_argument('--create-sample', action='store_true',
                        help='Create sample dataset for testing')
    args = parser.parse_args()
    
    print("="*60)
    print("[ML] FIRE DETECTION MODEL TRAINING")
    print("="*60)
    
    # Create sample dataset if requested
    if args.create_sample:
        create_sample_dataset(args.data_dir)
        print("\n[TIP] Now run without --create-sample to train")
        return 0
    
    try:
        # Initialize trainer
        trainer = FireModelTrainer(
            data_dir=args.data_dir,
            model_dir=args.model_dir
        )
        
        # Prepare dataset
        trainer.prepare_dataset(batch_size=args.batch_size)
        
        # Build model
        trainer.build_model(use_transfer_learning=not args.no_transfer)
        
        # Train
        trainer.train(epochs=args.epochs)
        
        # Fine-tune if requested
        if args.fine_tune and not args.no_transfer:
            trainer.fine_tune()
        
        # Evaluate
        trainer.evaluate()
        
        # Save models
        trainer.save_model()
        
        print("\n" + "="*60)
        print("[OK] TRAINING COMPLETE")
        print("="*60)
        print(f"\nTo use the model, update config/dfs_config.yaml:")
        print(f"  fire_detection:")
        print(f"    image_recognition:")
        print(f"      model_path: 'models/fire_detector.tflite'")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"\n[FAIL] {e}")
        print("\nTo create a sample dataset for testing:")
        print(f"  python {sys.argv[0]} --create-sample")
        return 1
    except Exception as e:
        print(f"\n[FAIL] Training failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
