"""
Type definitions for the lsfg-vk plugin responses.
"""

from typing import TypedDict, Optional, List, Dict, Any
from .config_schema import ConfigurationData


class BaseResponse(TypedDict):
    """Base response structure"""
    success: bool


class ErrorResponse(BaseResponse):
    """Response structure for errors"""
    error: str


class MessageResponse(BaseResponse):
    """Response structure with message"""
    message: str


class InstallationResponse(BaseResponse):
    """Response for installation operations"""
    message: str
    error: Optional[str]


class UninstallationResponse(BaseResponse):
    """Response for uninstallation operations"""
    message: str
    removed_files: Optional[List[str]]
    error: Optional[str]


class InstallationCheckResponse(TypedDict):
    """Response for installation check"""
    installed: bool
    lib_exists: bool
    json_exists: bool
    script_exists: bool
    lib_path: str
    json_path: str
    script_path: str
    error: Optional[str]


class DllDetectionResponse(TypedDict):
    """Response for DLL detection"""
    detected: bool
    path: Optional[str]
    source: Optional[str]
    message: Optional[str]
    error: Optional[str]


class ConfigurationResponse(BaseResponse):
    """Response for configuration operations"""
    config: Optional[ConfigurationData]
    message: Optional[str]
    error: Optional[str]


class ProfileConfig(TypedDict):
    """Configuration for a single profile"""
    exe: str
    config: ConfigurationData


class ProfilesResponse(BaseResponse):
    """Response for profile operations"""
    profiles: Optional[List[str]]
    current_profile: Optional[str]
    message: Optional[str]
    error: Optional[str]


class ProfileResponse(BaseResponse):
    """Response for single profile operations"""
    profile_name: Optional[str]
    message: Optional[str]
    error: Optional[str]
