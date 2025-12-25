"""
Download Fire Detection Dataset
Downloads sample fire/no-fire images for training
"""

import os
import sys
import urllib.request
import zipfile
import shutil
from pathlib import Path


def download_fire_dataset(output_dir='data/training_images'):
    """
    Download fire detection dataset from public sources
    Uses a curated subset for quick training
    """
    output_path = Path(output_dir)
    fire_dir = output_path / 'fire'
    no_fire_dir = output_path / 'no_fire'
    
    fire_dir.mkdir(parents=True, exist_ok=True)
    no_fire_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*60)
    print("[DOWNLOAD] Fire Detection Dataset")
    print("="*60)
    
    # Sample fire images from public domain sources
    fire_urls = [
        # Wikimedia Commons - public domain fire images
        ("https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/GolshanFire.jpg/640px-GolshanFire.jpg", "fire_001.jpg"),
        ("https://upload.wikimedia.org/wikipedia/commons/thumb/d/d1/Fire_inside_an_abandoned_convent_in_Massueville%2C_Quebec%2C_Canada.jpg/640px-Fire_inside_an_abandoned_convent_in_Massueville%2C_Quebec%2C_Canada.jpg", "fire_002.jpg"),
        ("https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Flames_in_Palo_Alto_Baylands.jpg/640px-Flames_in_Palo_Alto_Baylands.jpg", "fire_003.jpg"),
        ("https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/Wildfire_in_California.jpg/640px-Wildfire_in_California.jpg", "fire_004.jpg"),
        ("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/Fire_in_a_field.jpg/640px-Fire_in_a_field.jpg", "fire_005.jpg"),
        ("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Kontrolliertes_Feuer.jpg/640px-Kontrolliertes_Feuer.jpg", "fire_006.jpg"),
        ("https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Campfire_Pinecone.png/640px-Campfire_Pinecone.png", "fire_007.png"),
        ("https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Lagerfeuer_01.jpg/640px-Lagerfeuer_01.jpg", "fire_008.jpg"),
        ("https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Big_Burn.jpg/640px-Big_Burn.jpg", "fire_009.jpg"),
        ("https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Prescribed_burn_in_a_Pinus_nigra_stand_in_Portugal.JPG/640px-Prescribed_burn_in_a_Pinus_nigra_stand_in_Portugal.JPG", "fire_010.jpg"),
    ]
    
    # Sample no-fire images (nature, forests, buildings)
    no_fire_urls = [
        ("https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/24701-nature-702.jpg/640px-24701-nature-702.jpg", "no_fire_001.jpg"),
        ("https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg/640px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg", "no_fire_002.jpg"),
        ("https://upload.wikimedia.org/wikipedia/commons/thumb/b/b6/Image_created_with_a_mobile_phone.png/640px-Image_created_with_a_mobile_phone.png", "no_fire_003.png"),
        ("https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/640px-PNG_transparency_demonstration_1.png", "no_fire_004.png"),
        ("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Camponotus_flavomarginatus_ant.jpg/640px-Camponotus_flavomarginatus_ant.jpg", "no_fire_005.jpg"),
        ("https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Sunflower_from_Silesia.jpg/640px-Sunflower_from_Silesia.jpg", "no_fire_006.jpg"),
        ("https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/640px-Cat03.jpg", "no_fire_007.jpg"),
        ("https://upload.wikimedia.org/wikipedia/commons/thumb/b/bf/Bucephala-clangula-010.jpg/640px-Bucephala-clangula-010.jpg", "no_fire_008.jpg"),
        ("https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/The_Earth_seen_from_Apollo_17.jpg/640px-The_Earth_seen_from_Apollo_17.jpg", "no_fire_009.jpg"),
        ("https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/Tux.png/640px-Tux.png", "no_fire_010.png"),
    ]
    
    print(f"\n[FIRE] Downloading {len(fire_urls)} fire images...")
    downloaded_fire = download_images(fire_urls, fire_dir)
    
    print(f"\n[NO FIRE] Downloading {len(no_fire_urls)} no-fire images...")
    downloaded_no_fire = download_images(no_fire_urls, no_fire_dir)
    
    print(f"\n[OK] Downloaded {downloaded_fire} fire images")
    print(f"[OK] Downloaded {downloaded_no_fire} no-fire images")
    print(f"\n[TIP] For better results, add more images:")
    print(f"   - Download Kaggle fire dataset")
    print(f"   - Use: python ml_training/dataset_utils.py --augment 200")
    
    return downloaded_fire, downloaded_no_fire


def download_images(url_list, dest_dir):
    """Download images from URL list"""
    downloaded = 0
    
    for url, filename in url_list:
        dest_path = dest_dir / filename
        
        if dest_path.exists():
            print(f"   [SKIP] {filename} (exists)")
            downloaded += 1
            continue
        
        try:
            print(f"   [GET] {filename}...", end=" ", flush=True)
            
            # Create request with user agent
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; FireDetectionTrainer/1.0)'}
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                with open(dest_path, 'wb') as f:
                    f.write(response.read())
            
            print("[OK]")
            downloaded += 1
            
        except Exception as e:
            print(f"[FAIL] {e}")
    
    return downloaded


def download_kaggle_dataset(output_dir='data/training_images'):
    """
    Instructions for downloading Kaggle fire dataset
    Requires kaggle CLI and API key
    """
    print("""
[KAGGLE] Fire Dataset Download Instructions
==========================================

1. Install Kaggle CLI:
   pip install kaggle

2. Get API key:
   - Go to https://www.kaggle.com/settings
   - Click "Create New Token"
   - Save kaggle.json to ~/.kaggle/

3. Download dataset:
   kaggle datasets download -d phylake1337/fire-dataset
   unzip fire-dataset.zip -d data/kaggle_fire

4. Import into training:
   python ml_training/dataset_utils.py --import-fire data/kaggle_fire/fire_images
   python ml_training/dataset_utils.py --import-no-fire data/kaggle_fire/non_fire_images

5. Train model:
   python ml_training/train_fire_model.py --data-dir data/training_images
""")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Download fire detection dataset')
    parser.add_argument('--output', type=str, default='data/training_images',
                        help='Output directory')
    parser.add_argument('--kaggle', action='store_true',
                        help='Show Kaggle download instructions')
    args = parser.parse_args()
    
    if args.kaggle:
        download_kaggle_dataset(args.output)
        return 0
    
    download_fire_dataset(args.output)
    return 0


if __name__ == '__main__':
    sys.exit(main())
