#!/usr/bin/env python3
"""
Test script to debug profile detection while game is running
"""

import sys
import os
sys.path.append('py_modules')

from lsfg_vk.process_detection import ProcessDetectionService
from lsfg_vk.configuration import ConfigurationService

class TestLogger:
    def info(self, msg): 
        print(f'INFO: {msg}')
    def warning(self, msg): 
        print(f'WARNING: {msg}')
    def error(self, msg): 
        print(f'ERROR: {msg}')

def main():
    print("=== Testing Profile Detection ===")
    
    # Test process detection
    logger = TestLogger()
    process_service = ProcessDetectionService(logger)
    
    print("\n1. Testing get_current_active_profile():")
    active_profile = process_service.get_current_active_profile()
    print(f"Result: {active_profile}")
    
    print("\n2. Testing get_running_processes():")
    processes = process_service.get_running_processes()
    print(f"LSFG processes found: {len(processes.get('lsfg_processes', []))}")
    for proc in processes.get('lsfg_processes', []):
        print(f"  - PID {proc['pid']}: {proc['comm']} - {proc['args'][:100]}...")
    
    print(f"Regular processes found: {len(processes.get('processes', []))}")
    for proc in processes.get('processes', [])[:5]:  # Show first 5
        print(f"  - PID {proc['pid']}: {proc['comm']} - {proc['args'][:100]}...")
    
    print("\n3. Testing configuration service:")
    config_service = ConfigurationService()
    config_result = config_service.get_config()
    if config_result['success']:
        print("Current config loaded successfully")
        if config_result['config'].get('per_game_profiles'):
            print("Per-game profiles are enabled")
        else:
            print("Per-game profiles are disabled")
    else:
        print(f"Failed to load config: {config_result['error']}")

if __name__ == "__main__":
    main()
