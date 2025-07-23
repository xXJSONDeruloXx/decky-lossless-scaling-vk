#!/usr/bin/env python3

import os
import subprocess
from pathlib import Path

class MockLogger:
    def info(self, msg): print(f"INFO: {msg}")
    def warning(self, msg): print(f"WARNING: {msg}")
    def error(self, msg): print(f"ERROR: {msg}")

def get_clean_env():
    """Get a clean environment without conflicting library paths."""
    clean_env = os.environ.copy()
    for var in ['LD_LIBRARY_PATH', 'LD_PRELOAD', 'PYTHONPATH']:
        clean_env.pop(var, None)
    return clean_env

def check_flatpak_configured(app_id: str):
    """Test the flatpak configuration detection for a specific app."""
    logger = MockLogger()
    
    try:
        print(f"\nChecking configuration for {app_id}...")
        
        # Check if overrides exist
        result = subprocess.run(
            ["flatpak", "override", "--user", "--show", app_id],
            capture_output=True,
            text=True,
            check=False,
            env=get_clean_env()
        )
        
        if result.returncode != 0:
            print(f"  No overrides found (exit code: {result.returncode})")
            return False
            
        override_content = result.stdout
        print(f"  Override content: {override_content}")
        
        # Check for lsfg-vk related filesystem overrides
        required_paths = [
            ".config/lsfg-vk",
            "lib/liblsfg-vk.so", 
            "vulkan/implicit_layer.d"  # Updated to match both share/vulkan and config/vulkan
        ]
        
        for path in required_paths:
            if path in override_content:
                print(f"  ✓ Found required path: {path}")
            else:
                print(f"  ❌ Missing required path: {path}")
                return False
                
        print(f"  ✓ All required paths found - {app_id} is configured!")
        return True
        
    except Exception as e:
        logger.error(f"Error checking Flatpak configuration for {app_id}: {e}")
        return False

def check_symlinks_exist(app_id: str):
    """Check if the necessary symlinks exist for a Flatpak app."""
    print(f"\nChecking symlinks for {app_id}...")
    
    home_dir = Path.home()
    app_dir = home_dir / ".var" / "app" / app_id
    
    required_symlinks = [
        app_dir / "lib" / "liblsfg-vk.so",
        app_dir / "config" / "vulkan" / "implicit_layer.d" / "VkLayer_LS_frame_generation.json",
        app_dir / "config" / "lsfg-vk" / "conf.toml"
    ]
    
    all_exist = True
    for symlink_path in required_symlinks:
        if symlink_path.exists():
            print(f"  ✓ {symlink_path}")
        else:
            print(f"  ❌ {symlink_path}")
            all_exist = False
            
    return all_exist

def main():
    app_id = "com.heroicgameslauncher.hgl"
    
    print(f"Testing configuration detection for {app_id}")
    
    configured = check_flatpak_configured(app_id)
    symlinks_exist = check_symlinks_exist(app_id)
    
    print(f"\nSUMMARY:")
    print(f"  Configured: {configured}")
    print(f"  Symlinks exist: {symlinks_exist}")
    
    if configured and symlinks_exist:
        status = "Fully configured"
    elif configured or symlinks_exist:
        status = "Partially configured"
    else:
        status = "Not configured"
        
    print(f"  Overall status: {status}")

if __name__ == "__main__":
    main()
