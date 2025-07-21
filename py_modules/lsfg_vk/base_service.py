"""
Base service class with common functionality.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Any, Optional

from .constants import LOCAL_LIB, LOCAL_SHARE_BASE, VULKAN_LAYER_DIR, SCRIPT_NAME, CONFIG_DIR, CONFIG_FILENAME


class FallbackLogger:
    """Fallback logger when decky is not available"""
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.INFO)
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
    
    def info(self, msg: str) -> None:
        self._logger.info(msg)
    
    def error(self, msg: str) -> None:
        self._logger.error(msg)
    
    def warning(self, msg: str) -> None:
        self._logger.warning(msg)


class BaseService:
    """Base service class with common functionality"""
    
    def __init__(self, logger: Optional[Any] = None):
        """Initialize base service
        
        Args:
            logger: Logger instance, defaults to decky.logger if None, fallback logger if decky unavailable
        """
        if logger is None:
            try:
                import decky
                self.log = decky.logger
            except ImportError:
                # Use fallback logger when decky is not available (e.g., in launch script environment)
                self.log = FallbackLogger()
        else:
            self.log = logger
            
        # Initialize common paths using pathlib
        self.user_home = Path.home()
        self.local_lib_dir = self.user_home / LOCAL_LIB
        self.local_share_dir = self.user_home / VULKAN_LAYER_DIR
        self.lsfg_script_path = self.user_home / SCRIPT_NAME
        self.lsfg_launch_script_path = self.user_home / SCRIPT_NAME  # ~/lsfg launch script
        self.config_dir = self.user_home / CONFIG_DIR
        self.config_file_path = self.config_dir / CONFIG_FILENAME
    
    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist"""
        self.local_lib_dir.mkdir(parents=True, exist_ok=True)
        self.local_share_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.log.info(f"Ensured directories exist: {self.local_lib_dir}, {self.local_share_dir}, {self.config_dir}")
    
    def _remove_if_exists(self, path: Path) -> bool:
        """Remove a file if it exists
        
        Args:
            path: Path to the file to remove
            
        Returns:
            True if file was removed, False if it didn't exist
            
        Raises:
            OSError: If removal fails
        """
        if path.exists():
            try:
                path.unlink()
                self.log.info(f"Removed {path}")
                return True
            except OSError as e:
                self.log.error(f"Failed to remove {path}: {e}")
                raise
        else:
            self.log.info(f"File not found: {path}")
            return False
    
    def _write_file(self, path: Path, content: str, mode: int = 0o644) -> None:
        """Write content to a file
        
        Args:
            path: Target file path
            content: Content to write
            mode: File permissions (default: 0o644)
            
        Raises:
            OSError: If write fails
        """
        try:
            # Write directly to the file
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
                f.flush()  # Ensure data is written to disk
                os.fsync(f.fileno())  # Force filesystem sync
            
            # Set permissions
            path.chmod(mode)
            self.log.info(f"Wrote to {path}")
            
        except Exception:
            self.log.error(f"Failed to write to {path}")
            raise
