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
