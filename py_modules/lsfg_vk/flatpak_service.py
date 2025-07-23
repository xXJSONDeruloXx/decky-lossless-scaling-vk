"""
Service for managing Flatpak application integration with lsfg-vk.

This service provides methods to list, configure, and manage symlinks
for Flatpak applications that can use lsfg-vk.
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from .base_service import BaseService


class FlatpakService(BaseService):
    """Service for managing Flatpak integration with lsfg-vk."""
    
    # Known gaming Flatpak applications that can benefit from lsfg-vk
    SUPPORTED_FLATPAKS = [
        {
            "id": "com.heroicgameslauncher.hgl",
            "name": "Heroic Games Launcher",
            "needs_dll_override": True
        },
        {
            "id": "com.valvesoftware.Steam",
            "name": "Steam",
            "needs_dll_override": False
        },
        {
            "id": "net.lutris.Lutris",
            "name": "Lutris",
            "needs_dll_override": True
        },
        {
            "id": "org.prismlauncher.PrismLauncher",
            "name": "Prism Launcher",
            "needs_dll_override": True
        },
        {
            "id": "com.atlauncher.ATLauncher",
            "name": "ATLauncher",
            "needs_dll_override": True
        },
        {
            "id": "org.polymc.PolyMC",
            "name": "PolyMC",
            "needs_dll_override": True
        },
        {
            "id": "com.mojang.Minecraft",
            "name": "Minecraft",
            "needs_dll_override": True
        }
    ]
    
    def __init__(self):
        super().__init__()
        self.home_dir = Path.home()
        self.config_dir = self.home_dir / ".config" / "lsfg-vk"
        
    def _get_clean_env(self) -> Dict[str, str]:
        """Get a clean environment without conflicting library paths."""
        clean_env = os.environ.copy()
        # Remove potentially conflicting environment variables
        for var in ['LD_LIBRARY_PATH', 'LD_PRELOAD', 'PYTHONPATH']:
            clean_env.pop(var, None)
        return clean_env
        
    def is_flatpak_available(self) -> bool:
        """Check if Flatpak is available on the system."""
        try:
            result = subprocess.run(
                ["which", "flatpak"],
                capture_output=True,
                text=True,
                check=False,
                env=self._get_clean_env()
            )
            return result.returncode == 0
        except Exception as e:
            self.log.error(f"Error checking Flatpak availability: {e}")
            return False
    
    def get_installed_flatpaks(self) -> List[str]:
        """Get list of installed Flatpak application IDs."""
        if not self.is_flatpak_available():
            return []
            
        try:
            # First try the columns approach
            result = subprocess.run(
                ["flatpak", "list", "--app", "--columns=application"],
                capture_output=True,
                text=True,
                check=False,  # Don't raise exception on non-zero exit
                env=self._get_clean_env()
            )
            
            if result.returncode == 0:
                installed_ids = []
                lines = result.stdout.strip().split('\n')
                
                # Skip the header line "Application ID" if present
                for i, line in enumerate(lines):
                    line = line.strip()
                    if not line:
                        continue
                    # Skip the header line
                    if i == 0 and line == "Application ID":
                        continue
                    installed_ids.append(line)
                        
                return installed_ids
            else:
                # Log the error and try fallback method
                self.log.warning(f"Flatpak list with columns failed (exit {result.returncode}): {result.stderr}")
                
                # Fallback: use basic list and parse the first column
                result = subprocess.run(
                    ["flatpak", "list", "--app"],
                    capture_output=True,
                    text=True,
                    check=True,
                    env=self._get_clean_env()
                )
                
                installed_ids = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        # Parse the application ID (second column, tab-separated)
                        parts = line.strip().split('\t')
                        if len(parts) >= 2:
                            installed_ids.append(parts[1])  # App ID is in second column
                            
                return installed_ids
            
        except subprocess.CalledProcessError as e:
            self.log.error(f"Error getting installed Flatpaks: {e}")
            if hasattr(e, 'stderr') and e.stderr:
                self.log.error(f"Command stderr: {e.stderr}")
            return []
        except Exception as e:
            self.log.error(f"Unexpected error getting installed Flatpaks: {e}")
            return []
    
    def get_supported_flatpaks_status(self) -> List[Dict[str, Any]]:
        """Get status of supported Flatpak applications."""
        if not self.is_flatpak_available():
            return []
            
        installed_flatpaks = self.get_installed_flatpaks()
        flatpak_status = []
        
        for flatpak_info in self.SUPPORTED_FLATPAKS:
            app_id = flatpak_info["id"]
            is_installed = app_id in installed_flatpaks
            
            status = {
                "id": app_id,
                "name": flatpak_info["name"],
                "installed": is_installed,
                "needs_dll_override": flatpak_info["needs_dll_override"],
                "configured": False,
                "symlinks_exist": False
            }
            
            if is_installed:
                status["configured"] = self._check_flatpak_configured(app_id)
                status["symlinks_exist"] = self._check_symlinks_exist(app_id)
                
            flatpak_status.append(status)
            
        return flatpak_status
    
    def _check_flatpak_configured(self, app_id: str) -> bool:
        """Check if a Flatpak app has the necessary overrides configured."""
        try:
            # Check if overrides exist
            result = subprocess.run(
                ["flatpak", "override", "--user", "--show", app_id],
                capture_output=True,
                text=True,
                check=False,
                env=self._get_clean_env()
            )
            
            if result.returncode != 0:
                return False
                
            override_content = result.stdout
            
            # Check for lsfg-vk related filesystem overrides
            required_paths = [
                ".config/lsfg-vk",
                "lib/liblsfg-vk.so",
                "vulkan/implicit_layer.d"  # This matches both share/vulkan and config/vulkan paths
            ]
            
            for path in required_paths:
                if path not in override_content:
                    return False
                    
            return True
            
        except Exception as e:
            self.log.error(f"Error checking Flatpak configuration for {app_id}: {e}")
            return False
    
    def _check_symlinks_exist(self, app_id: str) -> bool:
        """Check if the necessary symlinks exist for a Flatpak app."""
        try:
            app_dir = self.home_dir / ".var" / "app" / app_id
            
            required_symlinks = [
                app_dir / "lib" / "liblsfg-vk.so",
                app_dir / "config" / "vulkan" / "implicit_layer.d" / "VkLayer_LS_frame_generation.json",
                app_dir / "config" / "lsfg-vk" / "conf.toml"
            ]
            
            for symlink_path in required_symlinks:
                if not symlink_path.exists():
                    return False
                    
            return True
            
        except Exception as e:
            self.log.error(f"Error checking symlinks for {app_id}: {e}")
            return False
    
    def _find_dll_path(self) -> Optional[str]:
        """Find the Lossless Scaling DLL path."""
        try:
            # Search for Lossless.dll
            result = subprocess.run(
                ["find", "/", "-name", "Lossless.dll", "-type", "f"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0 and result.stdout.strip():
                dll_path = result.stdout.strip().split('\n')[0]
                return str(Path(dll_path).parent)
                
            return None
            
        except Exception as e:
            self.log.error(f"Error finding DLL path: {e}")
            return None
    
    def configure_flatpak(self, app_id: str) -> Dict[str, Any]:
        """Configure a Flatpak application for lsfg-vk usage."""
        try:
            if not self.is_flatpak_available():
                return {
                    "success": False,
                    "error": "Flatpak is not available on this system"
                }
            
            # Check if app is installed
            installed_flatpaks = self.get_installed_flatpaks()
            if app_id not in installed_flatpaks:
                return {
                    "success": False,
                    "error": f"Flatpak {app_id} is not installed"
                }
            
            # Find app info
            app_info = None
            for flatpak_info in self.SUPPORTED_FLATPAKS:
                if flatpak_info["id"] == app_id:
                    app_info = flatpak_info
                    break
            
            if not app_info:
                return {
                    "success": False,
                    "error": f"Unsupported Flatpak application: {app_id}"
                }
            
            # Set up overrides and symlinks
            self._setup_flatpak_overrides(app_id, app_info["needs_dll_override"])
            self._setup_flatpak_symlinks(app_id)
            
            return {
                "success": True,
                "message": f"Successfully configured {app_info['name']} for lsfg-vk"
            }
            
        except Exception as e:
            self.log.error(f"Error configuring Flatpak {app_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _setup_flatpak_overrides(self, app_id: str, needs_dll_override: bool):
        """Set up Flatpak filesystem overrides."""
        # Base overrides that all apps need
        base_overrides = [
            "--filesystem=" + str(self.home_dir / ".config" / "lsfg-vk") + ":ro"
        ]
        
        # Check if using AUR/CachyOS package or manual installation
        if (Path("/usr/lib/liblsfg-vk.so").exists() and 
            Path("/etc/vulkan/implicit_layer.d/VkLayer_LS_frame_generation.json").exists()):
            # AUR/CachyOS package paths
            base_overrides.extend([
                "--filesystem=/usr/lib/liblsfg-vk.so:ro",
                "--filesystem=/etc/vulkan/implicit_layer.d/VkLayer_LS_frame_generation.json:ro"
            ])
        elif (Path(self.home_dir / ".local" / "lib" / "liblsfg-vk.so").exists() and 
              Path(self.home_dir / ".local" / "share" / "vulkan" / "implicit_layer.d" / "VkLayer_LS_frame_generation.json").exists()):
            # Manual installation paths
            base_overrides.extend([
                f"--filesystem={self.home_dir}/.local/lib/liblsfg-vk.so:ro",
                f"--filesystem={self.home_dir}/.local/share/vulkan/implicit_layer.d/VkLayer_LS_frame_generation.json:ro"
            ])
        
        # Add DLL path override if needed (not for Steam)
        if needs_dll_override:
            dll_path = self._find_dll_path()
            if dll_path:
                base_overrides.append(f"--filesystem={dll_path}:ro")
        
        # Apply overrides
        cmd = ["flatpak", "override", "--user"] + base_overrides + [app_id]
        
        subprocess.run(cmd, check=True, capture_output=True, env=self._get_clean_env())
    
    def _setup_flatpak_symlinks(self, app_id: str):
        """Set up symlinks for Flatpak application."""
        app_dir = self.home_dir / ".var" / "app" / app_id
        
        # Create necessary directories
        (app_dir / "lib").mkdir(parents=True, exist_ok=True)
        (app_dir / "config" / "vulkan" / "implicit_layer.d").mkdir(parents=True, exist_ok=True)
        (app_dir / "config" / "lsfg-vk").mkdir(parents=True, exist_ok=True)
        
        # Set up symlinks based on installation method
        if (Path("/usr/lib/liblsfg-vk.so").exists() and 
            Path("/etc/vulkan/implicit_layer.d/VkLayer_LS_frame_generation.json").exists()):
            # AUR/CachyOS package
            self._create_symlink(
                Path("/usr/lib/liblsfg-vk.so"),
                app_dir / "lib" / "liblsfg-vk.so"
            )
            self._create_symlink(
                Path("/etc/vulkan/implicit_layer.d/VkLayer_LS_frame_generation.json"),
                app_dir / "config" / "vulkan" / "implicit_layer.d" / "VkLayer_LS_frame_generation.json"
            )
        elif (Path(self.home_dir / ".local" / "lib" / "liblsfg-vk.so").exists() and 
              Path(self.home_dir / ".local" / "share" / "vulkan" / "implicit_layer.d" / "VkLayer_LS_frame_generation.json").exists()):
            # Manual installation
            self._create_symlink(
                self.home_dir / ".local" / "lib" / "liblsfg-vk.so",
                app_dir / "lib" / "liblsfg-vk.so"
            )
            self._create_symlink(
                self.home_dir / ".local" / "share" / "vulkan" / "implicit_layer.d" / "VkLayer_LS_frame_generation.json",
                app_dir / "config" / "vulkan" / "implicit_layer.d" / "VkLayer_LS_frame_generation.json"
            )
        
        # Config symlink (same for both installation methods)
        self._create_symlink(
            self.config_dir / "conf.toml",
            app_dir / "config" / "lsfg-vk" / "conf.toml"
        )
    
    def _create_symlink(self, source: Path, target: Path):
        """Create a symlink, removing existing target if necessary."""
        try:
            # Remove existing symlink or file
            if target.exists() or target.is_symlink():
                target.unlink()
            
            # Create symlink
            target.symlink_to(source)
            self.log.info(f"Created symlink: {target} -> {source}")
            
        except Exception as e:
            self.log.error(f"Error creating symlink {target} -> {source}: {e}")
    
    def remove_flatpak_configuration(self, app_id: str) -> Dict[str, Any]:
        """Remove lsfg-vk configuration from a Flatpak application."""
        try:
            if not self.is_flatpak_available():
                return {
                    "success": False,
                    "error": "Flatpak is not available on this system"
                }
            
            # Remove overrides
            subprocess.run(
                ["flatpak", "override", "--user", "--reset", app_id],
                check=True,
                capture_output=True,
                env=self._get_clean_env()
            )
            
            # Remove symlinks
            app_dir = self.home_dir / ".var" / "app" / app_id
            symlinks_to_remove = [
                app_dir / "lib" / "liblsfg-vk.so",
                app_dir / "config" / "vulkan" / "implicit_layer.d" / "VkLayer_LS_frame_generation.json",
                app_dir / "config" / "lsfg-vk" / "conf.toml"
            ]
            
            for symlink in symlinks_to_remove:
                try:
                    if symlink.exists() or symlink.is_symlink():
                        symlink.unlink()
                except Exception as e:
                    self.log.warning(f"Could not remove symlink {symlink}: {e}")
            
            # Find app name
            app_name = app_id
            for flatpak_info in self.SUPPORTED_FLATPAKS:
                if flatpak_info["id"] == app_id:
                    app_name = flatpak_info["name"]
                    break
            
            return {
                "success": True,
                "message": f"Removed lsfg-vk configuration from {app_name}"
            }
            
        except subprocess.CalledProcessError as e:
            self.log.error(f"Error removing Flatpak configuration for {app_id}: {e}")
            return {
                "success": False,
                "error": f"Failed to reset Flatpak overrides: {e}"
            }
        except Exception as e:
            self.log.error(f"Unexpected error removing Flatpak configuration for {app_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
