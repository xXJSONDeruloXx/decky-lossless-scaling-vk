"""
Configuration service for TOML-based lsfg configuration management.
"""

from pathlib import Path
from typing import Dict, Any

from .base_service import BaseService
from .config_schema import ConfigurationManager, ConfigurationData, CONFIG_SCHEMA
from .types import ConfigurationResponse


class ConfigurationService(BaseService):
    """Service for managing TOML-based lsfg configuration"""
    
    def get_config(self) -> ConfigurationResponse:
        """Read current TOML configuration merged with launch script environment variables
        
        Returns:
            ConfigurationResponse with current configuration or error
        """
        try:
            # Get TOML configuration (with defaults if file doesn't exist)
            if not self.config_file_path.exists():
                # Return default configuration with DLL detection if file doesn't exist
                from .dll_detection import DllDetectionService
                dll_service = DllDetectionService(self.log)
                toml_config = ConfigurationManager.get_defaults_with_dll_detection(dll_service)
            else:
                content = self.config_file_path.read_text(encoding='utf-8')
                toml_config = ConfigurationManager.parse_toml_content(content)
            
            # Get script environment variables (if script exists)
            script_values = {}
            if self.lsfg_script_path.exists():
                try:
                    script_content = self.lsfg_script_path.read_text(encoding='utf-8')
                    script_values = ConfigurationManager.parse_script_content(script_content)
                    self.log.info(f"Parsed script values: {script_values}")
                except Exception as e:
                    self.log.warning(f"Failed to parse launch script: {str(e)}")
            
            # Merge TOML config with script values
            config = ConfigurationManager.merge_config_with_script(toml_config, script_values)
            
            return {
                "success": True,
                "config": config,
                "message": None,
                "error": None
            }
            
        except (OSError, IOError) as e:
            error_msg = f"Error reading lsfg config: {str(e)}"
            self.log.error(error_msg)
            return {
                "success": False,
                "config": None,
                "message": None,
                "error": str(e)
            }
        except Exception as e:
            error_msg = f"Error parsing config file: {str(e)}"
            self.log.error(error_msg)
            # Return defaults with DLL detection if parsing fails
            from .dll_detection import DllDetectionService
            dll_service = DllDetectionService(self.log)
            config = ConfigurationManager.get_defaults_with_dll_detection(dll_service)
            return {
                "success": True,
                "config": config,
                "message": f"Using default configuration due to parse error: {str(e)}",
                "error": None
            }
    
    def update_config(self, dll: str, multiplier: int, flow_scale: float, 
                     performance_mode: bool, hdr_mode: bool, 
                     experimental_present_mode: str = "fifo", 
                     dxvk_frame_rate: int = 0,
                     enable_wow64: bool = False,
                     disable_steamdeck_mode: bool = False,
                     per_game_profiles: bool = False) -> ConfigurationResponse:
        """Update TOML configuration
        
        Args:
            dll: Path to Lossless.dll
            multiplier: LSFG multiplier value
            flow_scale: LSFG flow scale value
            performance_mode: Whether to enable performance mode
            hdr_mode: Whether to enable HDR mode
            experimental_present_mode: Experimental Vulkan present mode override
            dxvk_frame_rate: Frame rate cap for DirectX games, before frame multiplier (0 = disabled)
            enable_wow64: Whether to enable PROTON_USE_WOW64=1 for 32-bit games
            disable_steamdeck_mode: Whether to disable Steam Deck mode
            per_game_profiles: Whether to enable per-game profiles
            
        Returns:
            ConfigurationResponse with success status
        """
        try:
            # Create configuration from individual arguments
            config = ConfigurationManager.create_config_from_args(
                dll, multiplier, flow_scale, performance_mode, hdr_mode,
                experimental_present_mode, dxvk_frame_rate, enable_wow64, disable_steamdeck_mode, per_game_profiles
            )
            
            # Generate TOML content using centralized manager
            toml_content = ConfigurationManager.generate_toml_content(config)
            
            # Ensure config directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Write the updated config directly to preserve inode for file watchers
            self._write_file(self.config_file_path, toml_content, 0o644)
            
            # Update the launch script with the new configuration
            script_result = self.update_lsfg_script(config)
            if not script_result["success"]:
                self.log.warning(f"Failed to update launch script: {script_result['error']}")
            
            self.log.info(f"Updated lsfg TOML configuration: "
                         f"dll='{dll}', multiplier={multiplier}, flow_scale={flow_scale}, "
                         f"performance_mode={performance_mode}, hdr_mode={hdr_mode}, "
                         f"experimental_present_mode='{experimental_present_mode}', "
                         f"dxvk_frame_rate={dxvk_frame_rate}, "
                         f"enable_wow64={enable_wow64}, disable_steamdeck_mode={disable_steamdeck_mode}, "
                         f"per_game_profiles={per_game_profiles}")
            
            return {
                "success": True,
                "config": config,
                "message": "lsfg configuration updated successfully",
                "error": None
            }
            
        except (OSError, IOError) as e:
            error_msg = f"Error updating lsfg config: {str(e)}"
            self.log.error(error_msg)
            return {
                "success": False,
                "config": None,
                "message": None,
                "error": str(e)
            }
        except ValueError as e:
            error_msg = f"Invalid configuration arguments: {str(e)}"
            self.log.error(error_msg)
            return {
                "success": False,
                "config": None,
                "message": None,
                "error": str(e)
            }
    
    def update_dll_path(self, dll_path: str) -> ConfigurationResponse:
        """Update just the DLL path in the configuration
        
        Args:
            dll_path: Path to the Lossless.dll file
            
        Returns:
            ConfigurationResponse with success status
        """
        try:
            # Get current merged config (TOML + script)
            current_response = self.get_config()
            if not current_response["success"] or current_response["config"] is None:
                # If we can't read current config, use defaults with DLL detection
                from .dll_detection import DllDetectionService
                dll_service = DllDetectionService(self.log)
                config = ConfigurationManager.get_defaults_with_dll_detection(dll_service)
            else:
                config = current_response["config"]
            
            # Update just the DLL path
            config["dll"] = dll_path
            
            # Generate TOML content and write it
            toml_content = ConfigurationManager.generate_toml_content(config)
            
            # Ensure config directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Write the updated config directly to preserve inode for file watchers
            self._write_file(self.config_file_path, toml_content, 0o644)
            
            self.log.info(f"Updated DLL path in lsfg configuration: '{dll_path}'")
            
            return {
                "success": True,
                "config": config,
                "message": f"DLL path updated to: {dll_path}",
                "error": None
            }
            
        except Exception as e:
            error_msg = f"Error updating DLL path: {str(e)}"
            self.log.error(error_msg)
            return {
                "success": False,
                "config": None,
                "message": None,
                "error": str(e)
            }
    
    def update_lsfg_script(self, config: ConfigurationData) -> ConfigurationResponse:
        """Update the ~/lsfg launch script with current configuration
        
        Args:
            config: Configuration data to apply to the script
            
        Returns:
            ConfigurationResponse indicating success or failure
        """
        try:
            script_content = self._generate_script_content(config)
            
            # Write the script file
            self._write_file(self.lsfg_script_path, script_content, 0o755)
            
            self.log.info(f"Updated lsfg launch script at {self.lsfg_script_path}")
            
            return {
                "success": True,
                "config": config,
                "message": "Launch script updated successfully",
                "error": None
            }
            
        except Exception as e:
            error_msg = f"Error updating launch script: {str(e)}"
            self.log.error(error_msg)
            return {
                "success": False,
                "config": None,
                "message": None,
                "error": str(e)
            }
    
    def _generate_script_content(self, config: ConfigurationData) -> str:
        """Generate the content for the ~/lsfg launch script
        
        Args:
            config: Configuration data to apply to the script
            
        Returns:
            The complete script content as a string
        """
        lines = [
            "#!/bin/bash",
            "# lsfg-vk launch script generated by decky-lossless-scaling-vk plugin",
            "# This script sets up the environment for lsfg-vk to work with the plugin configuration",
            "launch_command=\"$@\"",
            "logger \"lsfg-vk-launch: game launch command is: $launch_command\"",
            "logger \"lsfg-vk-launch: executable is: $(basename \"$launch_command\")\"",
        ]
        
        # Add LSFG_PROCESS export - either default or per-game
        if config.get("per_game_profiles", False):
            lines.extend([
                "",
                "# Per-game profile detection and auto-creation",
                "game_exe=\"$(basename \"$launch_command\")\"",
                "# Extract .exe name if present",
                "if [[ \"$game_exe\" == *.exe ]]; then",
                "    # Remove .exe extension and sanitize for profile name",
                "    profile_name=\"$(echo \"${game_exe%.exe}\" | sed 's/[^a-zA-Z0-9_-]/-/g' | tr '[:upper:]' '[:lower:]')\"",
                "    export LSFG_PROCESS=\"$profile_name\"",
                "    logger \"lsfg-vk-launch: using per-game profile: $profile_name\"",
                "",
                "    # Auto-create profile if it doesn't exist - SYNCHRONOUS to ensure profile exists before game launch",
                "    config_dir=\"$HOME/.config/lsfg-vk\"", 
                "    config_file=\"$config_dir/conf.toml\"",
                "    if [[ -f \"$config_file\" ]] && ! grep -q \"exe = \\\"$profile_name\\\"\" \"$config_file\" 2>/dev/null; then",
                "        logger \"lsfg-vk-launch: auto-creating profile for $profile_name\"",
                "        # Trigger profile creation via Python script - WAIT for completion",
                "        python3 -c \"",
                "import sys; sys.path.append('/var/home/bazzite/decky-lossless-scaling-vk/py_modules')",
                "from lsfg_vk.configuration import ConfigurationService",
                "from lsfg_vk.config_schema import ConfigurationManager",
                "try:",
                "    service = ConfigurationService()",
                "    # Get current global config",
                "    current = service.get_config()",
                "    if current.get('success') and current.get('config'):",
                "        config = current['config']",
                "        config['per_game_profiles'] = True  # Ensure this stays on",
                "        result = service.update_game_profile('$profile_name', config)",
                "        if result.get('success'):",
                "            print(f'Profile $profile_name created successfully')",
                "        else:",
                "            print(f'Failed to create profile $profile_name: {result.get(\\\"error\\\", \\\"unknown error\\\")}')",
                "    else:",
                "        print('Failed to get current config for profile creation')",
                "except Exception as e:",
                "    print(f'Exception during profile creation: {e}')",
                "\"",
                "        if [ $? -eq 0 ]; then",
                "            logger \"lsfg-vk-launch: profile $profile_name created successfully\"",
                "        else",
                "            logger \"lsfg-vk-launch: failed to create profile $profile_name\"",
                "        fi",
                "    fi",
                "else",
                "    # Fallback to default for non-.exe files",
                "    export LSFG_PROCESS=decky-lsfg-vk",
                "    logger \"lsfg-vk-launch: using default profile (non-.exe executable)\"",
                "fi",
                ""
            ])
        else:
            lines.append("export LSFG_PROCESS=decky-lsfg-vk")
        
        # Add optional export statements based on configuration
        if config.get("enable_wow64", False):
            lines.append("export PROTON_USE_WOW64=1")
        
        if config.get("disable_steamdeck_mode", False):
            lines.append("export SteamDeck=0")
        
        # Add DXVK_FRAME_RATE if dxvk_frame_rate is set
        dxvk_frame_rate = config.get("dxvk_frame_rate", 0)
        if dxvk_frame_rate > 0:
            lines.append(f"export DXVK_FRAME_RATE={dxvk_frame_rate}")
        
        # Add the execution line
        lines.append('exec "$@"')
        
        return "\n".join(lines) + "\n"
    
    def get_game_profile(self, game_name: str) -> ConfigurationResponse:
        """Get configuration for a specific game profile
        
        Args:
            game_name: Name of the game profile to retrieve
            
        Returns:
            ConfigurationResponse with the game's configuration
        """
        try:
            if not self.config_file_path.exists():
                # Return default configuration if file doesn't exist
                from .dll_detection import DllDetectionService
                dll_service = DllDetectionService(self.log)
                config = ConfigurationManager.get_defaults_with_dll_detection(dll_service)
                return {
                    "success": True,
                    "config": config,
                    "message": f"Using default configuration for {game_name} (config file not found)",
                    "error": None
                }
            
            content = self.config_file_path.read_text(encoding='utf-8')
            global_config, game_profiles = ConfigurationManager.parse_per_game_toml_content(content)
            
            # Check if game profile exists
            if game_name in game_profiles:
                # Merge with global config (for dll path)
                game_config = game_profiles[game_name].copy()
                if global_config.get("dll"):
                    game_config["dll"] = global_config["dll"]
                game_config["per_game_profiles"] = global_config.get("per_game_profiles", False)
                
                return {
                    "success": True,
                    "config": game_config,
                    "message": f"Retrieved profile for {game_name}",
                    "error": None
                }
            else:
                # Return default config with dll from global
                config = ConfigurationManager.get_defaults()
                if global_config.get("dll"):
                    config["dll"] = global_config["dll"]
                config["per_game_profiles"] = global_config.get("per_game_profiles", False)
                
                return {
                    "success": True,
                    "config": config,
                    "message": f"Using default configuration for {game_name} (profile not found)",
                    "error": None
                }
            
        except Exception as e:
            error_msg = f"Error getting game profile for {game_name}: {str(e)}"
            self.log.error(error_msg)
            return {
                "success": False,
                "config": None,
                "message": None,
                "error": error_msg
            }
    
    def update_game_profile(self, game_name: str, config: ConfigurationData) -> ConfigurationResponse:
        """Update configuration for a specific game profile
        
        Args:
            game_name: Name of the game profile to update
            config: Configuration data for the game
            
        Returns:
            ConfigurationResponse with success status
        """
        try:
            # Read existing config or create new structure
            global_config = ConfigurationManager.get_defaults()
            game_profiles = {}
            
            if self.config_file_path.exists():
                content = self.config_file_path.read_text(encoding='utf-8')
                global_config, game_profiles = ConfigurationManager.parse_per_game_toml_content(content)
            
            # Update global config with dll and per_game_profiles setting
            global_config["dll"] = config.get("dll", global_config["dll"])
            global_config["per_game_profiles"] = config.get("per_game_profiles", False)
            
            # Update the specific game profile
            game_profiles[game_name] = config
            
            # Generate new TOML content
            toml_content = ConfigurationManager.generate_per_game_toml_content(global_config, game_profiles)
            
            # Ensure config directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Write the updated config
            self._write_file(self.config_file_path, toml_content, 0o644)
            
            # Update the launch script with the global configuration
            script_result = self.update_lsfg_script(global_config)
            if not script_result["success"]:
                self.log.warning(f"Failed to update launch script: {script_result['error']}")
            
            self.log.info(f"Updated game profile '{game_name}' with configuration")
            
            return {
                "success": True,
                "config": config,
                "message": f"Game profile '{game_name}' updated successfully",
                "error": None
            }
            
        except Exception as e:
            error_msg = f"Error updating game profile '{game_name}': {str(e)}"
            self.log.error(error_msg)
            return {
                "success": False,
                "config": None,
                "message": None,
                "error": error_msg
            }
    
    def list_game_profiles(self) -> Dict[str, Any]:
        """List all available game profiles
        
        Returns:
            Dict containing list of game profiles and global config
        """
        try:
            if not self.config_file_path.exists():
                return {
                    "success": True,
                    "global_config": ConfigurationManager.get_defaults(),
                    "game_profiles": {},
                    "message": "No configuration file found",
                    "error": None
                }
            
            content = self.config_file_path.read_text(encoding='utf-8')
            global_config, game_profiles = ConfigurationManager.parse_per_game_toml_content(content)
            
            return {
                "success": True,
                "global_config": global_config,
                "game_profiles": game_profiles,
                "message": f"Found {len(game_profiles)} game profiles",
                "error": None
            }
            
        except Exception as e:
            error_msg = f"Error listing game profiles: {str(e)}"
            self.log.error(error_msg)
            return {
                "success": False,
                "global_config": None,
                "game_profiles": {},
                "message": None,
                "error": error_msg
            }
