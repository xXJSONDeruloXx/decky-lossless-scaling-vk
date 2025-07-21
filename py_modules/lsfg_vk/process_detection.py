"""
Process detection service for per-game profiles.

This service handles detecting running game processes and matching them to configuration profiles.
"""

import re
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from .base_service import BaseService


class ProcessDetectionService(BaseService):
    """Service for detecting and managing game processes for per-game profiles"""
    
    def get_running_processes(self) -> Dict[str, Any]:
        """Get information about currently running processes
        
        Returns:
            Dict containing process information and matching details
        """
        try:
            # Get all running processes with their command lines
            result = subprocess.run([
                'ps', 'axo', 'pid,ppid,comm,args'
            ], capture_output=True, text=True, check=True)
            
            processes = []
            lsfg_processes = []
            
            for line in result.stdout.strip().split('\n')[1:]:  # Skip header
                parts = line.strip().split(None, 3)
                if len(parts) >= 4:
                    pid, ppid, comm, args = parts
                    
                    # Look for processes that might be games launched via our script
                    if 'lsfg' in args.lower() or 'LSFG_PROCESS' in args:
                        lsfg_processes.append({
                            'pid': pid,
                            'ppid': ppid,
                            'comm': comm,
                            'args': args
                        })
                    
                    # Look for game executables (common patterns)
                    if any(pattern in args.lower() for pattern in ['.exe', 'proton', 'steam']):
                        processes.append({
                            'pid': pid,
                            'ppid': ppid,
                            'comm': comm,
                            'args': args
                        })
            
            return {
                "success": True,
                "processes": processes[:20],  # Limit to first 20 for UI
                "lsfg_processes": lsfg_processes,
                "total_processes": len(processes),
                "error": None
            }
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to get process list: {str(e)}"
            self.log.error(error_msg)
            return {
                "success": False,
                "processes": [],
                "lsfg_processes": [],
                "total_processes": 0,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"Error getting processes: {str(e)}"
            self.log.error(error_msg)
            return {
                "success": False,
                "processes": [],
                "lsfg_processes": [],
                "total_processes": 0,
                "error": error_msg
            }
    
    def parse_launch_command_basename(self, launch_command: str) -> Optional[str]:
        """Extract the base executable name from a launch command
        
        Args:
            launch_command: The full launch command from the lsfg script logs
            
        Returns:
            The base executable name or None if not found
        """
        try:
            # Look for .exe files in the command
            exe_pattern = r'([^/\s]+\.exe)(?:\s|$)'
            exe_match = re.search(exe_pattern, launch_command, re.IGNORECASE)
            
            if exe_match:
                exe_name = exe_match.group(1)
                # Clean up the name (remove quotes, etc.)
                exe_name = exe_name.strip('"\'')
                return exe_name
            
            # Fallback: look for common executable patterns
            # Try to find the last component that looks like an executable
            parts = launch_command.split()
            for part in reversed(parts):
                # Skip common launcher prefixes
                if any(skip in part.lower() for skip in ['steam', 'proton', 'reaper', 'wrapper']):
                    continue
                
                # Look for file-like patterns
                if '/' in part and (part.endswith('.exe') or '.' in part.split('/')[-1]):
                    filename = part.split('/')[-1]
                    if filename and not filename.startswith('-'):
                        return filename.strip('"\'')
            
            return None
            
        except Exception as e:
            self.log.warning(f"Failed to parse launch command basename: {str(e)}")
            return None
    
    def sanitize_profile_name(self, exe_name: str) -> str:
        """Sanitize an executable name for use as a profile name
        
        Args:
            exe_name: The executable name to sanitize
            
        Returns:
            A sanitized profile name suitable for config files
        """
        # Remove .exe extension
        name = exe_name
        if name.lower().endswith('.exe'):
            name = name[:-4]
        
        # Replace spaces and special characters with hyphens
        name = re.sub(r'[^a-zA-Z0-9\-_]', '-', name)
        
        # Remove multiple consecutive hyphens
        name = re.sub(r'-+', '-', name)
        
        # Remove leading/trailing hyphens
        name = name.strip('-')
        
        # Ensure it's not empty
        if not name:
            name = "unknown-game"
        
        return name.lower()
    
    def get_last_launch_info(self) -> Dict[str, Any]:
        """Get information about the last launch from system logs
        
        Returns:
            Dict containing last launch command and extracted basename
        """
        try:
            # Look for recent lsfg-vk-launch log entries
            result = subprocess.run([
                'journalctl', '--user', '-n', '50', '--since', '1 hour ago'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                # Try system logs if user logs fail
                result = subprocess.run([
                    'journalctl', '-n', '50', '--since', '1 hour ago'
                ], capture_output=True, text=True)
            
            launch_commands = []
            basenames = []
            
            for line in result.stdout.split('\n'):
                if 'lsfg-vk-launch: game launch command is:' in line:
                    # Extract the command after the identifier
                    parts = line.split('lsfg-vk-launch: game launch command is:', 1)
                    if len(parts) > 1:
                        command = parts[1].strip()
                        launch_commands.append(command)
                        
                        # Parse basename
                        basename = self.parse_launch_command_basename(command)
                        if basename:
                            basenames.append(basename)
                
                elif 'lsfg-vk-launch: executable is:' in line:
                    # Extract basename directly from log
                    parts = line.split('lsfg-vk-launch: executable is:', 1)
                    if len(parts) > 1:
                        basename = parts[1].strip()
                        if basename and basename not in basenames:
                            basenames.append(basename)
            
            return {
                "success": True,
                "last_launch_command": launch_commands[-1] if launch_commands else None,
                "last_basename": basenames[-1] if basenames else None,
                "recent_basenames": list(set(basenames)),  # Remove duplicates
                "error": None
            }
            
        except Exception as e:
            error_msg = f"Failed to get launch info from logs: {str(e)}"
            self.log.warning(error_msg)
            return {
                "success": False,
                "last_launch_command": None,
                "last_basename": None,
                "recent_basenames": [],
                "error": error_msg
            }

    def get_current_active_profile(self) -> Optional[str]:
        """Get the currently active game profile by checking LSFG_PROCESS environment variable
        
        Based on lsfg-vk documentation: look for processes using Vulkan with LSFG_PROCESS set
        
        Returns:
            The active profile name or None if not found
        """
        try:
            self.log.info("Searching for active game profile...")
            
            # Look through all processes owned by current user that have Vulkan maps
            import os
            current_user = os.getenv('USER', 'unknown')
            
            vulkan_processes = []
            
            # Scan /proc for processes with Vulkan maps (lsfg-vk is a Vulkan layer)
            for proc_dir in Path('/proc').glob('[0-9]*'):
                try:
                    pid = proc_dir.name
                    
                    # Check if this process is owned by current user
                    stat_result = subprocess.run(['stat', '-c', '%U', str(proc_dir)], 
                                               capture_output=True, text=True)
                    if stat_result.returncode != 0 or stat_result.stdout.strip() != current_user:
                        continue
                    
                    # Check if process has Vulkan maps (indicating it's using Vulkan)
                    maps_file = proc_dir / 'maps'
                    if maps_file.exists():
                        try:
                            with open(maps_file, 'r') as f:
                                maps_content = f.read()
                                if 'vulkan' in maps_content.lower():
                                    # Get process name
                                    comm_file = proc_dir / 'comm'
                                    if comm_file.exists():
                                        proc_name = comm_file.read_text().strip()
                                        vulkan_processes.append({
                                            'pid': pid,
                                            'name': proc_name,
                                            'proc_dir': proc_dir
                                        })
                        except (PermissionError, FileNotFoundError, OSError):
                            continue
                            
                except (ValueError, PermissionError, FileNotFoundError, OSError):
                    continue
            
            self.log.info(f"Found {len(vulkan_processes)} Vulkan processes")
            for proc in vulkan_processes:
                self.log.info(f"  Vulkan process: PID {proc['pid']} - {proc['name']}")
            
            # Now check environment variables of Vulkan processes for LSFG_PROCESS
            for proc_info in vulkan_processes:
                try:
                    environ_file = proc_info['proc_dir'] / 'environ'
                    if environ_file.exists():
                        with open(environ_file, 'rb') as f:
                            environ_data = f.read().decode('utf-8', errors='ignore')
                            env_vars = environ_data.split('\0')
                            
                            # Log some environment variables for debugging
                            lsfg_vars = [var for var in env_vars if 'LSFG' in var or 'lsfg' in var.lower()]
                            if lsfg_vars:
                                self.log.info(f"  Process {proc_info['pid']} has LSFG-related env vars: {lsfg_vars}")
                            
                            for env_var in env_vars:
                                if env_var.startswith('LSFG_PROCESS='):
                                    profile_name = env_var.split('=', 1)[1]
                                    self.log.info(f"  Process {proc_info['pid']} has LSFG_PROCESS={profile_name}")
                                    # Skip the default profile
                                    if profile_name and profile_name != 'decky-lsfg-vk':
                                        self.log.info(f"Found active profile '{profile_name}' from Vulkan process {proc_info['pid']} ({proc_info['name']})")
                                        return profile_name
                                    else:
                                        self.log.info(f"Found default profile in process {proc_info['pid']} ({proc_info['name']}), continuing search...")
                except (PermissionError, FileNotFoundError, OSError) as e:
                    self.log.info(f"Could not read environment for process {proc_info['pid']}: {e}")
                    continue
            
            self.log.info("No active game profile found in Vulkan processes")
            return None
            
        except Exception as e:
            self.log.warning(f"Failed to get current active profile: {str(e)}")
            return None
