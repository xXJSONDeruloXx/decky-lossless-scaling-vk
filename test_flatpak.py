#!/usr/bin/env python3

import sys
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
    # Remove potentially conflicting environment variables
    for var in ['LD_LIBRARY_PATH', 'LD_PRELOAD', 'PYTHONPATH']:
        clean_env.pop(var, None)
    return clean_env

def test_flatpak_commands():
    logger = MockLogger()
    
    print("Testing Flatpak commands with clean environment...")
    
    try:
        # Test flatpak availability
        result = subprocess.run(
            ["which", "flatpak"],
            capture_output=True,
            text=True,
            check=False,
            env=get_clean_env()
        )
        print(f"Flatpak available: {result.returncode == 0}")
        
        if result.returncode == 0:
            # Test flatpak list with columns
            print("\nTesting flatpak list --columns=application...")
            result = subprocess.run(
                ["flatpak", "list", "--app", "--columns=application"],
                capture_output=True,
                text=True,
                check=False,
                env=get_clean_env()
            )
            
            if result.returncode == 0:
                print("SUCCESS - columns method works:")
                lines = result.stdout.strip().split('\n')
                for i, line in enumerate(lines[:10]):  # Show first 10 lines
                    if line.strip():
                        print(f"  {i}: '{line.strip()}'")
            else:
                print(f"FAILED - columns method (exit {result.returncode}): {result.stderr}")
                
                # Test fallback method
                print("\nTesting fallback: flatpak list --app...")
                result = subprocess.run(
                    ["flatpak", "list", "--app"],
                    capture_output=True,
                    text=True,
                    check=False,
                    env=get_clean_env()
                )
                
                if result.returncode == 0:
                    print("SUCCESS - fallback method works:")
                    lines = result.stdout.strip().split('\n')
                    for i, line in enumerate(lines[:5]):  # Show first 5 lines
                        if line.strip():
                            parts = line.strip().split('\t')
                            print(f"  {i}: App ID = '{parts[1] if len(parts) >= 2 else 'N/A'}' from '{line.strip()}'")
                else:
                    print(f"FAILED - fallback method (exit {result.returncode}): {result.stderr}")
                    
    except Exception as e:
        logger.error(f"Exception during testing: {e}")

if __name__ == "__main__":
    test_flatpak_commands()
