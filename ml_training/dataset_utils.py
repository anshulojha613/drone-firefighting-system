"""
Dataset Utilities for Fire Detection Model Training
Tools for downloading, organizing, and augmenting fire detection datasets
"""

import os
import sys
import shutil
import random
import argparse
from pathlib import Path

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


class DatasetManager:
    """Manages fire detection training datasets"""
    
    def __init__(self, data_dir='data/training_images'):
        self.data_dir = Path(data_dir)
        self.fire_dir = self.data_dir / 'fire'
        self.no_fire_dir = self.data_dir / 'no_fire'
    
    def setup_directories(self):
        """Create dataset directory structure"""
        self.fire_dir.mkdir(parents=True, exist_ok=True)
        self.no_fire_dir.mkdir(parents=True, exist_ok=True)
        print(f"[OK] Created directory structure at: {self.data_dir}")
        return self.data_dir
    
    def get_stats(self):
        """Get dataset statistics"""
        fire_images = list(self.fire_dir.glob('*.jpg')) + list(self.fire_dir.glob('*.png'))
        no_fire_images = list(self.no_fire_dir.glob('*.jpg')) + list(self.no_fire_dir.glob('*.png'))
        
        return {
            'fire_count': len(fire_images),
            'no_fire_count': len(no_fire_images),
            'total': len(fire_images) + len(no_fire_images),
            'fire_dir': str(self.fire_dir),
            'no_fire_dir': str(self.no_fire_dir)
        }
    
    def print_stats(self):
        """Print dataset statistics"""
        stats = self.get_stats()
        print(f"\n[STATS] Dataset: {self.data_dir}")
        print(f"   Fire images: {stats['fire_count']}")
        print(f"   No-fire images: {stats['no_fire_count']}")
        print(f"   Total: {stats['total']}")
        
        if stats['fire_count'] == 0 or stats['no_fire_count'] == 0:
            print("\n[WARN] Dataset incomplete. Need images in both categories.")
        
        return stats
    
    def import_images(self, source_dir, category, copy=True):
        """
        Import images from a source directory
        """
        source_path = Path(source_dir)
        
        if category == 'fire':
            dest_dir = self.fire_dir
        elif category == 'no_fire':
            dest_dir = self.no_fire_dir
        else:
            raise ValueError("Category must be 'fire' or 'no_fire'")
        
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # Find images
        images = list(source_path.glob('*.jpg')) + list(source_path.glob('*.png'))
        images += list(source_path.glob('*.jpeg')) + list(source_path.glob('*.JPG'))
        
        print(f"\n[IMPORT] Importing {len(images)} images to {category}/")
        
        imported = 0
        for img_path in images:
            dest_path = dest_dir / img_path.name
            
            # Handle duplicates
            if dest_path.exists():
                base = img_path.stem
                ext = img_path.suffix
                counter = 1
                while dest_path.exists():
                    dest_path = dest_dir / f"{base}_{counter}{ext}"
                    counter += 1
            
            if copy:
                shutil.copy2(img_path, dest_path)
            else:
                shutil.move(img_path, dest_path)
            imported += 1
        
        print(f"[OK] Imported {imported} images")
        return imported
    
    def augment_dataset(self, target_count=500):
        """
        Augment dataset to reach target count per category
        Uses basic transformations: flip, rotate, brightness
        """
        if not CV2_AVAILABLE:
            print("[FAIL] OpenCV required for augmentation. Install: pip install opencv-python")
            return
        
        print(f"\n[AUGMENT] Augmenting dataset to {target_count} images per category...")
        
        for category, cat_dir in [('fire', self.fire_dir), ('no_fire', self.no_fire_dir)]:
            images = list(cat_dir.glob('*.jpg')) + list(cat_dir.glob('*.png'))
            current_count = len(images)
            
            if current_count == 0:
                print(f"   [SKIP] No {category} images to augment")
                continue
            
            if current_count >= target_count:
                print(f"   [OK] {category}: {current_count} images (already >= {target_count})")
                continue
            
            needed = target_count - current_count
            print(f"   {category}: {current_count} -> {target_count} (generating {needed})")
            
            generated = 0
            while generated < needed:
                # Pick random source image
                src_img_path = random.choice(images)
                img = cv2.imread(str(src_img_path))
                
                if img is None:
                    continue
                
                # Apply random augmentation
                aug_type = random.choice(['flip_h', 'flip_v', 'rotate', 'brightness'])
                
                if aug_type == 'flip_h':
                    aug_img = cv2.flip(img, 1)
                elif aug_type == 'flip_v':
                    aug_img = cv2.flip(img, 0)
                elif aug_type == 'rotate':
                    angle = random.choice([90, 180, 270])
                    if angle == 90:
                        aug_img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
                    elif angle == 180:
                        aug_img = cv2.rotate(img, cv2.ROTATE_180)
                    else:
                        aug_img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
                elif aug_type == 'brightness':
                    factor = random.uniform(0.7, 1.3)
                    aug_img = cv2.convertScaleAbs(img, alpha=factor, beta=0)
                
                # Save augmented image
                aug_name = f"aug_{generated:04d}_{aug_type}.jpg"
                aug_path = cat_dir / aug_name
                cv2.imwrite(str(aug_path), aug_img)
                generated += 1
            
            print(f"   [OK] Generated {generated} augmented {category} images")
    
    def resize_images(self, size=(224, 224)):
        """Resize all images to target size"""
        if not CV2_AVAILABLE:
            print("[FAIL] OpenCV required. Install: pip install opencv-python")
            return
        
        print(f"\n[RESIZE] Resizing images to {size}...")
        
        for cat_dir in [self.fire_dir, self.no_fire_dir]:
            if not cat_dir.exists():
                continue
            
            images = list(cat_dir.glob('*.jpg')) + list(cat_dir.glob('*.png'))
            resized = 0
            
            for img_path in images:
                img = cv2.imread(str(img_path))
                if img is None:
                    continue
                
                if img.shape[:2] != size:
                    img_resized = cv2.resize(img, size)
                    cv2.imwrite(str(img_path), img_resized)
                    resized += 1
            
            print(f"   [OK] Resized {resized} images in {cat_dir.name}/")
    
    def split_dataset(self, test_ratio=0.2, output_dir=None):
        """
        Split dataset into train/test sets
        """
        if output_dir is None:
            output_dir = self.data_dir / 'split'
        else:
            output_dir = Path(output_dir)
        
        train_dir = output_dir / 'train'
        test_dir = output_dir / 'test'
        
        print(f"\n[SPLIT] Splitting dataset ({1-test_ratio:.0%} train, {test_ratio:.0%} test)...")
        
        for category in ['fire', 'no_fire']:
            src_dir = self.data_dir / category
            
            if not src_dir.exists():
                continue
            
            images = list(src_dir.glob('*.jpg')) + list(src_dir.glob('*.png'))
            random.shuffle(images)
            
            split_idx = int(len(images) * (1 - test_ratio))
            train_images = images[:split_idx]
            test_images = images[split_idx:]
            
            # Create directories
            (train_dir / category).mkdir(parents=True, exist_ok=True)
            (test_dir / category).mkdir(parents=True, exist_ok=True)
            
            # Copy images
            for img in train_images:
                shutil.copy2(img, train_dir / category / img.name)
            for img in test_images:
                shutil.copy2(img, test_dir / category / img.name)
            
            print(f"   {category}: {len(train_images)} train, {len(test_images)} test")
        
        print(f"[OK] Split dataset saved to: {output_dir}")
        return train_dir, test_dir
    
    def validate_images(self):
        """Check all images are valid and readable"""
        if not CV2_AVAILABLE:
            print("[FAIL] OpenCV required. Install: pip install opencv-python")
            return
        
        print("\n[VALIDATE] Checking image integrity...")
        
        bad = []
        for cat_dir in [self.fire_dir, self.no_fire_dir]:
            if not cat_dir.exists():
                continue
            
            images = list(cat_dir.glob('*.jpg')) + list(cat_dir.glob('*.png'))
            
            for img_path in images:
                img = cv2.imread(str(img_path))
                if img is None:
                    bad.append(img_path)
        
        if bad:
            print(f"[WARN] Found {len(bad)} bad images:")
            for path in bad[:10]:
                print(f"   - {path}")
            if len(bad) > 10:
                print(f"   ... and {len(bad) - 10} more")
        else:
            print("[OK] All images valid")
        
        return bad


def print_dataset_sources():
    """Print information about fire detection datasets"""
    print("""
[INFO] Fire Detection Dataset Sources
=====================================

1. Kaggle Fire Dataset
   URL: https://www.kaggle.com/datasets/phylake1337/fire-dataset
   Contains: ~1000 fire and non-fire images
   
2. FLAME Dataset
   URL: https://ieee-dataport.org/open-access/flame-dataset
   Contains: Aerial fire images from drones
   
3. BoWFire Dataset
   URL: https://bitbucket.org/gbdi/bowfire-dataset
   Contains: Fire images for early detection
   
4. Custom Collection
   - Capture images from drone during test flights
   - Use thermal camera output
   - Screenshot from fire videos

[TIP] Organize downloaded images into:
   data/training_images/
       fire/       <- Images containing fire
       no_fire/    <- Images without fire (nature, buildings, etc.)
""")


def main():
    parser = argparse.ArgumentParser(description='Fire detection dataset utilities')
    parser.add_argument('--data-dir', type=str, default='data/training_images',
                        help='Dataset directory')
    parser.add_argument('--setup', action='store_true',
                        help='Create directory structure')
    parser.add_argument('--stats', action='store_true',
                        help='Show dataset statistics')
    parser.add_argument('--import-fire', type=str,
                        help='Import fire images from directory')
    parser.add_argument('--import-no-fire', type=str,
                        help='Import no-fire images from directory')
    parser.add_argument('--augment', type=int, metavar='COUNT',
                        help='Augment dataset to COUNT images per category')
    parser.add_argument('--resize', type=int, nargs=2, metavar=('W', 'H'),
                        help='Resize all images to WxH')
    parser.add_argument('--split', type=float, metavar='RATIO',
                        help='Split dataset (RATIO = test fraction, e.g., 0.2)')
    parser.add_argument('--validate', action='store_true',
                        help='Validate all images are readable')
    parser.add_argument('--sources', action='store_true',
                        help='Show dataset download sources')
    args = parser.parse_args()
    
    if args.sources:
        print_dataset_sources()
        return 0
    
    manager = DatasetManager(args.data_dir)
    
    if args.setup:
        manager.setup_directories()
    
    if args.import_fire:
        manager.import_images(args.import_fire, 'fire')
    
    if args.import_no_fire:
        manager.import_images(args.import_no_fire, 'no_fire')
    
    if args.augment:
        manager.augment_dataset(target_count=args.augment)
    
    if args.resize:
        manager.resize_images(size=tuple(args.resize))
    
    if args.split:
        manager.split_dataset(test_ratio=args.split)
    
    if args.validate:
        manager.validate_images()
    
    if args.stats or not any([args.setup, args.import_fire, args.import_no_fire, 
                              args.augment, args.resize, args.split, args.validate]):
        manager.print_stats()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
