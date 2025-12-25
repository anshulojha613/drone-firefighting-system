#!/usr/bin/env python3
"""
Fix DroneKit for Python 3.13 Compatibility
Patches collections.MutableMapping -> collections.abc.MutableMapping
"""

import os
import sys

def find_dronekit_path():
    """Find the dronekit installation path without importing it"""
    # Find site-packages directory
    for path in sys.path:
        if 'site-packages' in path:
            dronekit_path = os.path.join(path, 'dronekit')
            if os.path.exists(dronekit_path):
                return dronekit_path
    
    print("[ERROR] DroneKit not found in site-packages")
    print("   Searched paths:")
    for path in sys.path:
        if 'site-packages' in path:
            print(f"   - {path}")
    sys.exit(1)

def patch_dronekit():
    """Patch DroneKit __init__.py for Python 3.13"""
    
    dronekit_path = find_dronekit_path()
    init_file = os.path.join(dronekit_path, '__init__.py')
    
    print(f"[DIR] DroneKit path: {dronekit_path}")
    print(f"[NOTE] Patching file: {init_file}")
    
    # Read the file
    try:
        with open(init_file, 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"[ERROR] Error reading file: {e}")
        sys.exit(1)
    
    # Check if already patched
    if 'collections.abc.MutableMapping' in content:
        print("[PASS] DroneKit already patched!")
        return
    
    # Make backup
    backup_file = init_file + '.backup'
    try:
        with open(backup_file, 'w') as f:
            f.write(content)
        print(f"[SAVE] Backup created: {backup_file}")
    except Exception as e:
        print(f"[WARN]  Warning: Could not create backup: {e}")
    
    # Apply patches
    patches_applied = 0
    
    # Patch 1: Add import for collections.abc
    if 'import collections.abc' not in content:
        # Find the imports section (after docstring, before first class/function)
        import_section_end = content.find('\nclass ')
        if import_section_end == -1:
            import_section_end = content.find('\ndef ')
        
        if import_section_end > 0:
            # Insert after existing imports
            insert_pos = content.rfind('\nimport ', 0, import_section_end)
            if insert_pos > 0:
                next_newline = content.find('\n', insert_pos + 1)
                content = content[:next_newline] + '\nimport collections.abc' + content[next_newline:]
                patches_applied += 1
                print("[OK] Added 'import collections.abc'")
    
    # Patch 2: Replace collections.MutableMapping with collections.abc.MutableMapping
    original_count = content.count('collections.MutableMapping')
    content = content.replace('collections.MutableMapping', 'collections.abc.MutableMapping')
    replaced_count = original_count - content.count('collections.MutableMapping')
    
    if replaced_count > 0:
        patches_applied += replaced_count
        print(f"[OK] Replaced {replaced_count} occurrences of 'collections.MutableMapping'")
    
    # Write patched content
    if patches_applied > 0:
        try:
            with open(init_file, 'w') as f:
                f.write(content)
            print(f"\n[PASS] Successfully patched DroneKit! ({patches_applied} changes)")
            print("\nTest with: python -c \"import dronekit; print('[OK] DroneKit working')\"")
        except Exception as e:
            print(f"[ERROR] Error writing patched file: {e}")
            print(f"Restoring from backup...")
            try:
                with open(backup_file, 'r') as f:
                    original = f.read()
                with open(init_file, 'w') as f:
                    f.write(original)
                print("[OK] Restored from backup")
            except:
                print("[ERROR] Could not restore backup")
            sys.exit(1)
    else:
        print("ℹ  No patches needed")

if __name__ == '__main__':
    print("="*70)
    print("  DroneKit Python 3.13 Compatibility Patch")
    print("="*70)
    print()
    
    patch_dronekit()
    
    print()
    print("="*70)
    print("  Testing DroneKit Import")
    print("="*70)
    
    try:
        import dronekit
        print("[PASS] DroneKit imports OK!")
        print(f"   Version: {dronekit.__version__ if hasattr(dronekit, '__version__') else 'unknown'}")
    except Exception as e:
        print(f"[ERROR] DroneKit import failed: {e}")
        sys.exit(1)
