"""
Configuration service for TOML-based lsfg configuration management.
"""

from pathlib import Path
from typing import Dict, Any

from .base_service import BaseService
from .config_schema import ConfigurationManager, CONFIG_SCHEMA, ProfileData, DEFAULT_PROFILE_NAME
from .config_schema_generated import ConfigurationData, get_script_generation_logic
from .configuration_helpers_generated import log_configuration_update
from .types import ConfigurationResponse, ProfilesResponse, ProfileResponse


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
            
            return self._success_response(ConfigurationResponse, config=config)
            
        except (OSError, IOError) as e:
            error_msg = f"Error reading lsfg config: {str(e)}"
            self.log.error(error_msg)
            return self._error_response(ConfigurationResponse, str(e), config=None)
        except Exception as e:
            error_msg = f"Error parsing config file: {str(e)}"
            self.log.error(error_msg)
            # Return defaults with DLL detection if parsing fails
            from .dll_detection import DllDetectionService
            dll_service = DllDetectionService(self.log)
            config = ConfigurationManager.get_defaults_with_dll_detection(dll_service)
            return self._success_response(ConfigurationResponse, 
                                        f"Using default configuration due to parse error: {str(e)}", 
                                        config=config)
    
    def update_config_from_dict(self, config: ConfigurationData) -> ConfigurationResponse:
        """Update TOML configuration from configuration dictionary (eliminates parameter duplication)
        
        Args:
            config: Complete configuration data dictionary
            
        Returns:
            ConfigurationResponse with success status
        """
        try:
            profile_data = self._get_profile_data()
            current_profile = profile_data["current_profile"]
            
            # Update the current profile's config
            return self.update_profile_config(current_profile, config)
            
        except (OSError, IOError) as e:
            error_msg = f"Error updating lsfg config: {str(e)}"
            self.log.error(error_msg)
            return self._error_response(ConfigurationResponse, str(e), config=None)
        except ValueError as e:
            error_msg = f"Invalid configuration arguments: {str(e)}"
            self.log.error(error_msg)
            return self._error_response(ConfigurationResponse, str(e), config=None)
    
    def update_config(self, **kwargs) -> ConfigurationResponse:
        """Update TOML configuration using generated schema - SIMPLIFIED WITH GENERATED CODE
        
        Args:
            **kwargs: Configuration field values (see shared_config.py for available fields)
            
        Returns:
            ConfigurationResponse with success status
        """
        try:
            # Create configuration from keyword arguments using generated function
            config = ConfigurationManager.create_config_from_args(**kwargs)
            
            # Update using the new profile-aware method
            return self.update_config_from_dict(config)
            
        except (OSError, IOError) as e:
            error_msg = f"Error updating lsfg config: {str(e)}"
            self.log.error(error_msg)
            return self._error_response(ConfigurationResponse, str(e), config=None)
        except ValueError as e:
            error_msg = f"Invalid configuration arguments: {str(e)}"
            self.log.error(error_msg)
            return self._error_response(ConfigurationResponse, str(e), config=None)
    
    def update_dll_path(self, dll_path: str) -> ConfigurationResponse:
        """Update just the DLL path in the configuration
        
        Args:
            dll_path: Path to the Lossless.dll file
            
        Returns:
            ConfigurationResponse with success status
        """
        try:
            profile_data = self._get_profile_data()
            
            # Update global config (DLL path is global)
            profile_data["global_config"]["dll"] = dll_path
            
            # Also update current profile's config for backward compatibility
            current_profile = profile_data["current_profile"]
            from .config_schema_generated import DLL
            profile_data["profiles"][current_profile][DLL] = dll_path
            
            # Save to file
            self._save_profile_data(profile_data)
            
            # Update launch script
            script_result = self.update_lsfg_script_from_profile_data(profile_data)
            if not script_result["success"]:
                self.log.warning(f"Failed to update launch script: {script_result['error']}")
            
            self.log.info(f"Updated DLL path in lsfg configuration: '{dll_path}'")
            
            return self._success_response(ConfigurationResponse,
                                        f"DLL path updated to: {dll_path}",
                                        config=profile_data["profiles"][current_profile])
            
        except Exception as e:
            error_msg = f"Error updating DLL path: {str(e)}"
            self.log.error(error_msg)
            return self._error_response(ConfigurationResponse, str(e), config=None)
    
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
            
            return self._success_response(ConfigurationResponse,
                                        "Launch script updated successfully",
                                        config=config)
            
        except Exception as e:
            error_msg = f"Error updating launch script: {str(e)}"
            self.log.error(error_msg)
            return self._error_response(ConfigurationResponse, str(e), config=None)
    
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
            "# This script sets up the environment for lsfg-vk to work with the plugin configuration"
        ]
        
        # Use auto-generated script generation logic
        generate_script_lines = get_script_generation_logic()
        lines.extend(generate_script_lines(config))
        
        # Add LSFG_PROCESS export with override support
        lines.extend([
            "",
            "# Check if script was called with override syntax (e.g., ~/lsfg=profile_name)",
            "if [[ \"$0\" == *\"=\"* ]]; then",
            "    # Extract override value from script name",
            "    OVERRIDE_PROCESS=\"${0##*=}\"",
            "    export LSFG_PROCESS=\"$OVERRIDE_PROCESS\"",
            "else",
            "    # Use default profile",
            "    export LSFG_PROCESS=decky-lsfg-vk",
            "fi",
            "",
            'exec "$@"'
        ])
        
        return "\n".join(lines) + "\n"
    
    def _generate_script_content_for_profile(self, profile_data: ProfileData) -> str:
        """Generate the content for the ~/lsfg launch script with profile support
        
        Args:
            profile_data: Profile data containing current profile and configurations
            
        Returns:
            The complete script content as a string
        """
        current_profile = profile_data["current_profile"]
        config = profile_data["profiles"].get(current_profile, ConfigurationManager.get_defaults())
        
        # Merge global config with profile config
        merged_config = dict(config)
        for field_name, value in profile_data["global_config"].items():
            merged_config[field_name] = value
        
        lines = [
            "#!/bin/bash",
            "# lsfg-vk launch script generated by decky-lossless-scaling-vk plugin",
            f"# Current profile: {current_profile}",
            "# This script sets up the environment for lsfg-vk to work with the plugin configuration"
        ]
        
        # Use auto-generated script generation logic
        generate_script_lines = get_script_generation_logic()
        lines.extend(generate_script_lines(merged_config))
        
        # Add LSFG_PROCESS export with override support
        override_logic = [
            "",
            "# Check if script was called with override syntax (e.g., ~/lsfg=profile_name)",
            "if [[ \"$0\" == *\"=\"* ]]; then",
            "    # Extract override value from script name",
            "    OVERRIDE_PROCESS=\"${0##*=}\"",
            "    export LSFG_PROCESS=\"$OVERRIDE_PROCESS\"",
            "else",
            "    # Use current profile as default",
            f"    export LSFG_PROCESS={current_profile}",
            "fi",
            "",
            'exec "$@"'
        ]
        lines.extend(override_logic)
        
        return "\n".join(lines) + "\n"
    
    def _get_profile_data(self) -> ProfileData:
        """Get current profile data from config file"""
        if not self.config_file_path.exists():
            # Return default profile structure if file doesn't exist
            from .dll_detection import DllDetectionService
            dll_service = DllDetectionService(self.log)
            default_config = ConfigurationManager.get_defaults_with_dll_detection(dll_service)
            return ProfileData(
                current_profile=DEFAULT_PROFILE_NAME,
                profiles={DEFAULT_PROFILE_NAME: default_config},
                global_config={
                    "dll": default_config.get("dll", ""),
                    "no_fp16": default_config.get("no_fp16", False)
                }
            )
        
        content = self.config_file_path.read_text(encoding='utf-8')
        return ConfigurationManager.parse_toml_content_multi_profile(content)
    
    def _save_profile_data(self, profile_data: ProfileData) -> None:
        """Save profile data to config file"""
        toml_content = ConfigurationManager.generate_toml_content_multi_profile(profile_data)
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Write the updated config directly to preserve inode for file watchers
        self._write_file(self.config_file_path, toml_content, 0o644)
    
    # Profile management methods
    def get_profiles(self) -> ProfilesResponse:
        """Get list of all profiles and current profile
        
        Returns:
            ProfilesResponse with profile list and current profile
        """
        try:
            profile_data = self._get_profile_data()
            
            return self._success_response(ProfilesResponse,
                                        "Profiles retrieved successfully",
                                        profiles=list(profile_data["profiles"].keys()),
                                        current_profile=profile_data["current_profile"])
            
        except Exception as e:
            error_msg = f"Error getting profiles: {str(e)}"
            self.log.error(error_msg)
            return self._error_response(ProfilesResponse, str(e), 
                                       profiles=None, current_profile=None)
    
    def create_profile(self, profile_name: str, source_profile: str = None) -> ProfileResponse:
        """Create a new profile
        
        Args:
            profile_name: Name for the new profile
            source_profile: Optional source profile to copy from (default: current profile)
            
        Returns:
            ProfileResponse with success status
        """
        try:
            profile_data = self._get_profile_data()
            
            # Use current profile as source if not specified
            if not source_profile:
                source_profile = profile_data["current_profile"]
            
            # Create the new profile
            new_profile_data = ConfigurationManager.create_profile(profile_data, profile_name, source_profile)
            
            # Save to file
            self._save_profile_data(new_profile_data)
            
            self.log.info(f"Created profile '{profile_name}' from '{source_profile}'")
            
            return self._success_response(ProfileResponse,
                                        f"Profile '{profile_name}' created successfully",
                                        profile_name=profile_name)
            
        except ValueError as e:
            error_msg = f"Invalid profile operation: {str(e)}"
            self.log.error(error_msg)
            return self._error_response(ProfileResponse, str(e), profile_name=None)
        except Exception as e:
            error_msg = f"Error creating profile: {str(e)}"
            self.log.error(error_msg)
            return self._error_response(ProfileResponse, str(e), profile_name=None)
    
    def delete_profile(self, profile_name: str) -> ProfileResponse:
        """Delete a profile
        
        Args:
            profile_name: Name of the profile to delete
            
        Returns:
            ProfileResponse with success status
        """
        try:
            profile_data = self._get_profile_data()
            
            # Delete the profile
            new_profile_data = ConfigurationManager.delete_profile(profile_data, profile_name)
            
            # Save to file
            self._save_profile_data(new_profile_data)
            
            # Update launch script if current profile changed
            script_result = self.update_lsfg_script_from_profile_data(new_profile_data)
            if not script_result["success"]:
                self.log.warning(f"Failed to update launch script: {script_result['error']}")
            
            self.log.info(f"Deleted profile '{profile_name}'")
            
            return self._success_response(ProfileResponse,
                                        f"Profile '{profile_name}' deleted successfully",
                                        profile_name=profile_name)
            
        except ValueError as e:
            error_msg = f"Invalid profile operation: {str(e)}"
            self.log.error(error_msg)
            return self._error_response(ProfileResponse, str(e), profile_name=None)
        except Exception as e:
            error_msg = f"Error deleting profile: {str(e)}"
            self.log.error(error_msg)
            return self._error_response(ProfileResponse, str(e), profile_name=None)
    
    def rename_profile(self, old_name: str, new_name: str) -> ProfileResponse:
        """Rename a profile
        
        Args:
            old_name: Current profile name
            new_name: New profile name
            
        Returns:
            ProfileResponse with success status
        """
        try:
            profile_data = self._get_profile_data()
            
            # Rename the profile
            new_profile_data = ConfigurationManager.rename_profile(profile_data, old_name, new_name)
            
            # Save to file
            self._save_profile_data(new_profile_data)
            
            # Update launch script if current profile changed
            script_result = self.update_lsfg_script_from_profile_data(new_profile_data)
            if not script_result["success"]:
                self.log.warning(f"Failed to update launch script: {script_result['error']}")
            
            self.log.info(f"Renamed profile '{old_name}' to '{new_name}'")
            
            return self._success_response(ProfileResponse,
                                        f"Profile renamed from '{old_name}' to '{new_name}' successfully",
                                        profile_name=new_name)
            
        except ValueError as e:
            error_msg = f"Invalid profile operation: {str(e)}"
            self.log.error(error_msg)
            return self._error_response(ProfileResponse, str(e), profile_name=None)
        except Exception as e:
            error_msg = f"Error renaming profile: {str(e)}"
            self.log.error(error_msg)
            return self._error_response(ProfileResponse, str(e), profile_name=None)
    
    def set_current_profile(self, profile_name: str) -> ProfileResponse:
        """Set the current active profile
        
        Args:
            profile_name: Name of the profile to set as current
            
        Returns:
            ProfileResponse with success status
        """
        try:
            profile_data = self._get_profile_data()
            
            # Set current profile
            new_profile_data = ConfigurationManager.set_current_profile(profile_data, profile_name)
            
            # Save to file
            self._save_profile_data(new_profile_data)
            
            # Update launch script with new current profile
            script_result = self.update_lsfg_script_from_profile_data(new_profile_data)
            if not script_result["success"]:
                self.log.warning(f"Failed to update launch script: {script_result['error']}")
            
            self.log.info(f"Set current profile to '{profile_name}'")
            
            return self._success_response(ProfileResponse,
                                        f"Current profile set to '{profile_name}' successfully",
                                        profile_name=profile_name)
            
        except ValueError as e:
            error_msg = f"Invalid profile operation: {str(e)}"
            self.log.error(error_msg)
            return self._error_response(ProfileResponse, str(e), profile_name=None)
        except Exception as e:
            error_msg = f"Error setting current profile: {str(e)}"
            self.log.error(error_msg)
            return self._error_response(ProfileResponse, str(e), profile_name=None)
    
    def update_profile_config(self, profile_name: str, config: ConfigurationData) -> ConfigurationResponse:
        """Update configuration for a specific profile
        
        Args:
            profile_name: Name of the profile to update
            config: Configuration data to apply
            
        Returns:
            ConfigurationResponse with success status
        """
        try:
            profile_data = self._get_profile_data()
            
            if profile_name not in profile_data["profiles"]:
                return self._error_response(ConfigurationResponse, 
                                          f"Profile '{profile_name}' does not exist", 
                                          config=None)
            
            # Update the profile's config
            profile_data["profiles"][profile_name] = config
            
            # Update global config fields if they're in the config
            for field_name in ["dll", "no_fp16"]:
                if field_name in config:
                    profile_data["global_config"][field_name] = config[field_name]
            
            # Save to file
            self._save_profile_data(profile_data)
            
            # Update launch script if this is the current profile
            if profile_name == profile_data["current_profile"]:
                script_result = self.update_lsfg_script_from_profile_data(profile_data)
                if not script_result["success"]:
                    self.log.warning(f"Failed to update launch script: {script_result['error']}")
            
            # Log with dynamic field listing
            field_values = ", ".join(f"{k}={repr(v)}" for k, v in config.items())
            self.log.info(f"Updated profile '{profile_name}' configuration: {field_values}")
            
            return self._success_response(ConfigurationResponse,
                                        f"Profile '{profile_name}' configuration updated successfully",
                                        config=config)
            
        except Exception as e:
            error_msg = f"Error updating profile configuration: {str(e)}"
            self.log.error(error_msg)
            return self._error_response(ConfigurationResponse, str(e), config=None)
    
    def update_lsfg_script_from_profile_data(self, profile_data: ProfileData) -> ConfigurationResponse:
        """Update the ~/lsfg launch script from profile data
        
        Args:
            profile_data: Profile data to apply to the script
            
        Returns:
            ConfigurationResponse indicating success or failure
        """
        try:
            script_content = self._generate_script_content_for_profile(profile_data)
            
            # Write the script file
            self._write_file(self.lsfg_script_path, script_content, 0o755)
            
            self.log.info(f"Updated lsfg launch script at {self.lsfg_script_path} for profile '{profile_data['current_profile']}'")
            
            # Get current profile config for response
            current_config = profile_data["profiles"].get(profile_data["current_profile"], ConfigurationManager.get_defaults())
            
            return self._success_response(ConfigurationResponse,
                                        "Launch script updated successfully",
                                        config=current_config)
            
        except Exception as e:
            error_msg = f"Error updating launch script: {str(e)}"
            self.log.error(error_msg)
            return self._error_response(ConfigurationResponse, str(e), config=None)
