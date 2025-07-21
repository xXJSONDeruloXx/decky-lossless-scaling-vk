"""
Centralized configuration schema for lsfg-vk.

This module defines the complete configuration structure for lsfg-vk, managing TOML-based config files, including:
- Field definitions with types, defaults, and metadata
- TOML generation logic
- Validation rules
- Type definitions
"""

import re
from typing import TypedDict, Dict, Any, Union, cast
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ConfigFieldType(Enum):
    """Supported configuration field types"""
    BOOLEAN = "boolean"
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"


@dataclass
class ConfigField:
    """Configuration field definition"""
    name: str
    field_type: ConfigFieldType
    default: Union[bool, int, float, str]
    description: str
    
    def get_toml_value(self, value: Union[bool, int, float, str]) -> Union[bool, int, float, str]:
        """Get the value for TOML output"""
        return value


# Configuration schema definition
CONFIG_SCHEMA: Dict[str, ConfigField] = {
    "dll": ConfigField(
        name="dll",
        field_type=ConfigFieldType.STRING,
        default="",  # Will be populated dynamically based on detection
        description="specify where Lossless.dll is stored"
    ),
    
    "multiplier": ConfigField(
        name="multiplier",
        field_type=ConfigFieldType.INTEGER,
        default=1,
        description="change the fps multiplier"
    ),
    
    "flow_scale": ConfigField(
        name="flow_scale",
        field_type=ConfigFieldType.FLOAT,
        default=0.8,
        description="change the flow scale"
    ),
    
    "performance_mode": ConfigField(
        name="performance_mode",
        field_type=ConfigFieldType.BOOLEAN,
        default=True,
        description="toggle performance mode"
    ),
    
    "hdr_mode": ConfigField(
        name="hdr_mode",
        field_type=ConfigFieldType.BOOLEAN,
        default=False,
        description="enable hdr mode"
    ),
    
    "experimental_present_mode": ConfigField(
        name="experimental_present_mode",
        field_type=ConfigFieldType.STRING,
        default="fifo",
        description="experimental: override vulkan present mode (fifo/mailbox/immediate)"
    ),
}

# Fields that should ONLY be in the lsfg script, not in TOML config
SCRIPT_ONLY_FIELDS = {
    "dxvk_frame_rate": ConfigField(
        name="dxvk_frame_rate",
        field_type=ConfigFieldType.INTEGER,
        default=0,
        description="base framerate cap for DirectX games, before frame multiplier (0 = disabled, requires game re-launch)"
    ),
    
    "enable_wow64": ConfigField(
        name="enable_wow64",
        field_type=ConfigFieldType.BOOLEAN,
        default=False,
        description="enable PROTON_USE_WOW64=1 for 32-bit games (use with ProtonGE to fix crashing)"
    ),
    
    "disable_steamdeck_mode": ConfigField(
        name="disable_steamdeck_mode",
        field_type=ConfigFieldType.BOOLEAN,
        default=False,
        description="disable Steam Deck mode (unlocks hidden settings in some games)"
    )
}

# Complete configuration schema (TOML + script-only fields)
COMPLETE_CONFIG_SCHEMA = {**CONFIG_SCHEMA, **SCRIPT_ONLY_FIELDS}

# Per-game profile fields
PER_GAME_FIELDS = {
    "per_game_profiles": ConfigField(
        name="per_game_profiles",
        field_type=ConfigFieldType.BOOLEAN,
        default=False,
        description="enable per-game profiles instead of global configuration"
    )
}

# Complete schema including per-game fields
FULL_CONFIG_SCHEMA = {**COMPLETE_CONFIG_SCHEMA, **PER_GAME_FIELDS}


class ConfigurationData(TypedDict):
    """Type-safe configuration data structure"""
    dll: str
    multiplier: int
    flow_scale: float
    performance_mode: bool
    hdr_mode: bool
    experimental_present_mode: str
    dxvk_frame_rate: int
    enable_wow64: bool
    disable_steamdeck_mode: bool
    per_game_profiles: bool


class ConfigurationManager:
    """Centralized configuration management"""
    
    @staticmethod
    def get_defaults() -> ConfigurationData:
        """Get default configuration values"""
        return cast(ConfigurationData, {
            field.name: field.default 
            for field in FULL_CONFIG_SCHEMA.values()
        })
    
    @staticmethod
    def get_defaults_with_dll_detection(dll_detection_service=None) -> ConfigurationData:
        """Get default configuration values with DLL path detection
        
        Args:
            dll_detection_service: Optional DLL detection service instance
            
        Returns:
            ConfigurationData with detected DLL path if available
        """
        defaults = ConfigurationManager.get_defaults()
        
        # Try to detect DLL path if service provided
        if dll_detection_service:
            try:
                dll_result = dll_detection_service.check_lossless_scaling_dll()
                if dll_result.get("detected") and dll_result.get("path"):
                    defaults["dll"] = dll_result["path"]
            except Exception:
                # If detection fails, keep empty default
                pass
        
        # If DLL path is still empty, use a reasonable fallback
        if not defaults["dll"]:
            defaults["dll"] = "/home/deck/.local/share/Steam/steamapps/common/Lossless Scaling/Lossless.dll"
        
        return defaults
    
    @staticmethod
    def get_field_names() -> list[str]:
        """Get ordered list of configuration field names"""
        return list(FULL_CONFIG_SCHEMA.keys())
    
    @staticmethod
    def get_field_types() -> Dict[str, ConfigFieldType]:
        """Get field type mapping"""
        return {
            field.name: field.field_type 
            for field in FULL_CONFIG_SCHEMA.values()
        }
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> ConfigurationData:
        """Validate and convert configuration data"""
        validated = {}
        
        for field_name, field_def in FULL_CONFIG_SCHEMA.items():
            value = config.get(field_name, field_def.default)
            
            # Type validation and conversion
            if field_def.field_type == ConfigFieldType.BOOLEAN:
                validated[field_name] = bool(value)
            elif field_def.field_type == ConfigFieldType.INTEGER:
                validated[field_name] = int(value)
            elif field_def.field_type == ConfigFieldType.FLOAT:
                validated[field_name] = float(value)
            elif field_def.field_type == ConfigFieldType.STRING:
                validated[field_name] = str(value)
            else:
                validated[field_name] = value
        
        return cast(ConfigurationData, validated)
    
    @staticmethod
    def generate_toml_content(config: ConfigurationData) -> str:
        """Generate TOML configuration file content using the new game-specific format"""
        lines = ["version = 1"]
        lines.append("")
        
        # Add global section with DLL path only (if specified)
        if config.get("dll"):
            lines.append("[global]")
            lines.append("# Global settings")
            lines.append(f"# specify where Lossless.dll is stored")
            lines.append(f'dll = "{config["dll"]}"')
            # Always comment out per_game_profiles to avoid lsfg-vk component conflicts
            # but still track the state internally in the plugin
            per_game_enabled = config.get("per_game_profiles", False)
            lines.append(f"# Enable per-game profiles")
            lines.append(f'# per_game_profiles = {str(per_game_enabled).lower()}')
            lines.append("")
        
        # Add game section with process name for LSFG_PROCESS approach
        lines.append("[[game]]")
        lines.append("# Plugin-managed game entry (uses LSFG_PROCESS=decky-lsfg-vk)")
        lines.append('exe = "decky-lsfg-vk"')
        lines.append("")
        
        # Add all configuration fields to the game section
        for field_name, field_def in CONFIG_SCHEMA.items():
            # Skip dll field - dll goes in global section
            if field_name == "dll":
                continue
                
            value = config[field_name]
            
            # Add field description comment
            lines.append(f"# {field_def.description}")
            
            # Format value based on type
            if isinstance(value, bool):
                lines.append(f"{field_name} = {str(value).lower()}")
            elif isinstance(value, str) and value:  # Only add non-empty strings
                lines.append(f'{field_name} = "{value}"')
            elif isinstance(value, (int, float)):  # Always include numbers, even if 0 or 1
                lines.append(f"{field_name} = {value}")
            
            lines.append("")  # Empty line for readability
        
        return "\n".join(lines)
    
    @staticmethod
    def parse_toml_content(content: str) -> ConfigurationData:
        """Parse TOML content into configuration data using simple regex parsing"""
        config = ConfigurationManager.get_defaults()
        
        try:
            # Look for both [global] and [[game]] sections
            lines = content.split('\n')
            in_global_section = False
            in_game_section = False
            current_game_exe = None
            
            for line in lines:
                line = line.strip()
                
                # Handle per_game_profiles specially - parse both commented and uncommented versions
                # This allows the plugin to track the state even when commented out for lsfg-vk compatibility
                if line.startswith('# per_game_profiles =') or line.startswith('per_game_profiles ='):
                    # Extract the value whether it's commented or not
                    if line.startswith('# per_game_profiles ='):
                        value_part = line[len('# per_game_profiles ='):].strip()
                    else:
                        value_part = line[len('per_game_profiles ='):].strip()
                    
                    # Parse the boolean value
                    config["per_game_profiles"] = value_part.lower() in ('true', '1', 'yes', 'on')
                    continue
                
                # Skip comments and empty lines for regular parsing
                if not line or line.startswith('#'):
                    continue
                
                # Check for section headers
                if line.startswith('[') and line.endswith(']'):
                    if line == '[global]':
                        in_global_section = True
                        in_game_section = False
                    elif line == '[[game]]':
                        in_global_section = False
                        in_game_section = True
                        current_game_exe = None
                    else:
                        in_global_section = False
                        in_game_section = False
                    continue
                
                # Parse key = value lines
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes from string values
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    # Handle global section (dll only - per_game_profiles handled above)
                    if in_global_section:
                        if key == "dll":
                            config["dll"] = value
                    
                    # Handle game section
                    elif in_game_section:
                        # Track the exe for this game section
                        if key == "exe":
                            current_game_exe = value
                        # Only parse config for our plugin-managed game entry
                        elif current_game_exe == "decky-lsfg-vk" and key in CONFIG_SCHEMA:
                            field_def = CONFIG_SCHEMA[key]
                            try:
                                if field_def.field_type == ConfigFieldType.BOOLEAN:
                                    config[key] = value.lower() in ('true', '1', 'yes', 'on')
                                elif field_def.field_type == ConfigFieldType.INTEGER:
                                    parsed_value = int(value)
                                    config[key] = parsed_value
                                elif field_def.field_type == ConfigFieldType.FLOAT:
                                    config[key] = float(value)
                                elif field_def.field_type == ConfigFieldType.STRING:
                                    config[key] = value
                            except (ValueError, TypeError):
                                # If conversion fails, keep default value
                                pass
            
            return config
            
        except Exception:
            # If parsing fails completely, return defaults
            return ConfigurationManager.get_defaults()
    
    @staticmethod
    def parse_script_content(script_content: str) -> Dict[str, Union[bool, int, str]]:
        """Parse launch script content to extract environment variable values
        
        Args:
            script_content: Content of the launch script file
            
        Returns:
            Dict containing parsed script-only field values
        """
        script_values = {}
        
        try:
            lines = script_content.split('\n')
            
            for line in lines:
                line = line.strip()
                
                # Skip comments, empty lines, and non-export lines
                if not line or line.startswith('#') or not line.startswith('export '):
                    continue
                
                # Parse export statements: export VAR=value
                if '=' in line:
                    # Remove 'export ' prefix
                    export_line = line[len('export '):]
                    key, value = export_line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Map environment variables to config field names
                    if key == "DXVK_FRAME_RATE":
                        try:
                            script_values["dxvk_frame_rate"] = int(value)
                        except ValueError:
                            pass
                    elif key == "PROTON_USE_WOW64":
                        script_values["enable_wow64"] = value == "1"
                    elif key == "SteamDeck":
                        script_values["disable_steamdeck_mode"] = value == "0"
            
        except (ValueError, KeyError, IndexError) as e:
            # If parsing fails, log the error and return empty dict (will use defaults)
            print(f"Error parsing script content: {e}")
        
        return script_values
    
    @staticmethod
    def merge_config_with_script(toml_config: ConfigurationData, script_values: Dict[str, Union[bool, int, str]]) -> ConfigurationData:
        """Merge TOML configuration with script environment variable values
        
        Args:
            toml_config: Configuration loaded from TOML file
            script_values: Environment variable values parsed from script
            
        Returns:
            Complete configuration with script values overlaid on TOML config
        """
        merged_config = dict(toml_config)
        
        # Update script-only fields with values from script
        for field_name in SCRIPT_ONLY_FIELDS.keys():
            if field_name in script_values:
                merged_config[field_name] = script_values[field_name]
        
        return cast(ConfigurationData, merged_config)

    @staticmethod
    def create_config_from_args(dll: str, multiplier: int, flow_scale: float, 
                               performance_mode: bool, hdr_mode: bool, 
                               experimental_present_mode: str = "fifo", 
                               dxvk_frame_rate: int = 0,
                               enable_wow64: bool = False,
                               disable_steamdeck_mode: bool = False,
                               per_game_profiles: bool = False) -> ConfigurationData:
        """Create configuration from individual arguments"""
        return cast(ConfigurationData, {
            "dll": dll,
            "multiplier": multiplier,
            "flow_scale": flow_scale,
            "performance_mode": performance_mode,
            "hdr_mode": hdr_mode,
            "experimental_present_mode": experimental_present_mode,
            "dxvk_frame_rate": dxvk_frame_rate,
            "enable_wow64": enable_wow64,
            "disable_steamdeck_mode": disable_steamdeck_mode,
            "per_game_profiles": per_game_profiles
        })

    @staticmethod
    def generate_per_game_toml_content(config: ConfigurationData, game_profiles: Dict[str, ConfigurationData]) -> str:
        """Generate TOML configuration file content with per-game profiles
        
        Args:
            config: Global configuration (used for defaults and DLL path)
            game_profiles: Dict mapping game names to their configurations
            
        Returns:
            Complete TOML content with global and per-game sections
        """
        lines = ["version = 1"]
        lines.append("")
        
        # Add global section with DLL path and per-game toggle
        lines.append("[global]")
        lines.append("# Global settings")
        if config.get("dll"):
            lines.append(f"# specify where Lossless.dll is stored")
            lines.append(f'dll = "{config["dll"]}"')
        
        # Always comment out per_game_profiles to avoid lsfg-vk component conflicts
        # but still track the state internally in the plugin
        per_game_enabled = config.get("per_game_profiles", False)
        lines.append(f"# Enable per-game profiles")
        lines.append(f'# per_game_profiles = {str(per_game_enabled).lower()}')
        lines.append("")
        
        # Check if we already have a "decky-lsfg-vk" profile in game_profiles
        default_profile_name = "decky-lsfg-vk"
        if default_profile_name not in game_profiles:
            # Add default profile (used when per-game is disabled or as fallback)
            lines.append("[[game]]")
            lines.append("# Default profile (uses LSFG_PROCESS=decky-lsfg-vk)")
            lines.append('exe = "decky-lsfg-vk"')
            lines.append("")
            
            # Add configuration fields to default profile
            for field_name, field_def in CONFIG_SCHEMA.items():
                if field_name == "dll":  # Skip dll field - it's in global
                    continue
                    
                value = config[field_name]
                
                # Add field description comment
                lines.append(f"# {field_def.description}")
                
                # Format value based on type
                if isinstance(value, bool):
                    lines.append(f"{field_name} = {str(value).lower()}")
                elif isinstance(value, str) and value:
                    lines.append(f'{field_name} = "{value}"')
                elif isinstance(value, (int, float)):
                    lines.append(f"{field_name} = {value}")
                
                lines.append("")
        
        # Add per-game profiles
        for game_name, game_config in game_profiles.items():
            lines.append("[[game]]")
            if game_name == default_profile_name:
                lines.append(f"# Default profile (uses LSFG_PROCESS=decky-lsfg-vk)")
            else:
                lines.append(f"# Profile for {game_name}")
            lines.append(f'exe = "{game_name}"')
            lines.append("")
            
            # Add configuration fields to game profile
            for field_name, field_def in CONFIG_SCHEMA.items():
                if field_name == "dll":  # Skip dll field - it's in global
                    continue
                    
                value = game_config[field_name]
                
                # Add field description comment
                lines.append(f"# {field_def.description}")
                
                # Format value based on type
                if isinstance(value, bool):
                    lines.append(f"{field_name} = {str(value).lower()}")
                elif isinstance(value, str) and value:
                    lines.append(f'{field_name} = "{value}"')
                elif isinstance(value, (int, float)):
                    lines.append(f"{field_name} = {value}")
                
                lines.append("")
        
        return "\n".join(lines)

    @staticmethod 
    def parse_per_game_toml_content(content: str) -> tuple[ConfigurationData, Dict[str, ConfigurationData]]:
        """Parse TOML content with per-game profiles
        
        Args:
            content: TOML file content
            
        Returns:
            Tuple of (global_config, game_profiles_dict)
        """
        global_config = ConfigurationManager.get_defaults()
        game_profiles = {}
        
        try:
            lines = content.split('\n')
            in_global_section = False
            in_game_section = False
            current_game_exe = None
            current_game_config = None
            
            for line in lines:
                line = line.strip()
                
                # Handle per_game_profiles specially - parse both commented and uncommented versions
                # This allows the plugin to track the state even when commented out for lsfg-vk compatibility
                if line.startswith('# per_game_profiles =') or line.startswith('per_game_profiles ='):
                    # Extract the value whether it's commented or not
                    if line.startswith('# per_game_profiles ='):
                        value_part = line[len('# per_game_profiles ='):].strip()
                    else:
                        value_part = line[len('per_game_profiles ='):].strip()
                    
                    # Parse the boolean value
                    global_config["per_game_profiles"] = value_part.lower() in ('true', '1', 'yes', 'on')
                    continue
                
                # Skip comments and empty lines for regular parsing
                if not line or line.startswith('#'):
                    continue
                
                # Check for section headers
                if line.startswith('[') and line.endswith(']'):
                    # Save previous game profile if it exists
                    if in_game_section and current_game_exe and current_game_config:
                        game_profiles[current_game_exe] = current_game_config
                    
                    if line == '[global]':
                        in_global_section = True
                        in_game_section = False
                        current_game_exe = None
                        current_game_config = None
                    elif line == '[[game]]':
                        in_global_section = False
                        in_game_section = True
                        current_game_exe = None
                        current_game_config = ConfigurationManager.get_defaults()
                    else:
                        in_global_section = False
                        in_game_section = False
                        current_game_exe = None
                        current_game_config = None
                    continue
                
                # Parse key = value lines
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes from string values
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    # Handle global section (dll only - per_game_profiles handled above)
                    if in_global_section:
                        if key == "dll":
                            global_config["dll"] = value
                    
                    # Handle game section
                    elif in_game_section and current_game_config is not None:
                        if key == "exe":
                            current_game_exe = value
                        else:
                            # Parse configuration field if it exists in schema
                            if key in CONFIG_SCHEMA:
                                field_def = CONFIG_SCHEMA[key]
                                try:
                                    if field_def.field_type == ConfigFieldType.BOOLEAN:
                                        current_game_config[key] = value.lower() == "true"
                                    elif field_def.field_type == ConfigFieldType.INTEGER:
                                        current_game_config[key] = int(value)
                                    elif field_def.field_type == ConfigFieldType.FLOAT:
                                        current_game_config[key] = float(value)
                                    else:  # STRING
                                        current_game_config[key] = value
                                except (ValueError, TypeError):
                                    # Use default if parsing fails
                                    current_game_config[key] = field_def.default
            
            # Save the last game profile if it exists
            if in_game_section and current_game_exe and current_game_config:
                game_profiles[current_game_exe] = current_game_config
            
        except Exception as e:
            print(f"Error parsing per-game TOML content: {e}")
        
        return global_config, game_profiles
