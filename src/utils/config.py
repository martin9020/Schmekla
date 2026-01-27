"""
Configuration management for Schmekla.

Handles loading, saving, and accessing application configuration.
"""

from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass, field
import yaml
from loguru import logger


@dataclass
class UIConfig:
    """UI-related configuration."""
    theme: str = "dark"
    viewport_background: str = "#2b2b2b"
    grid_visible: bool = True
    axes_visible: bool = True
    default_dock_layout: str = "default"


@dataclass
class UnitsConfig:
    """Units configuration."""
    length: str = "mm"  # mm, m, in, ft
    angle: str = "deg"  # deg, rad
    force: str = "kN"   # N, kN, lbf, kip


@dataclass
class ExportConfig:
    """Export configuration."""
    ifc_schema: str = "IFC2X3"
    ifc_include_grids: bool = True
    ifc_include_levels: bool = True
    default_export_dir: str = ""


@dataclass
class ClaudeConfig:
    """Claude integration configuration."""
    enabled: bool = True
    timeout_seconds: int = 120
    max_history_length: int = 50
    auto_execute_commands: bool = False  # Require confirmation


@dataclass
class Config:
    """Main application configuration."""
    ui: UIConfig = field(default_factory=UIConfig)
    units: UnitsConfig = field(default_factory=UnitsConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    claude: ClaudeConfig = field(default_factory=ClaudeConfig)

    # Recent files
    recent_files: list = field(default_factory=list)
    max_recent_files: int = 10

    # Paths
    profile_catalog_path: str = ""
    material_catalog_path: str = ""
    data_path: str = ""

    _config_path: Path = field(default=None, repr=False)

    @classmethod
    def load(cls, config_path: Path = None) -> "Config":
        """
        Load configuration from file and .env.

        Args:
            config_path: Path to config file. Defaults to ~/.schmekla/config.yaml

        Returns:
            Config instance
        """
        if config_path is None:
            config_path = Path.home() / ".schmekla" / "config.yaml"

        config = cls()
        config._config_path = config_path

        # Load from config.yaml
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    data = yaml.safe_load(f)

                if data:
                    config._update_from_dict(data)
                    logger.debug(f"Configuration loaded from {config_path}")

            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
                logger.info("Using default configuration")
        else:
            logger.info(f"No config file found at {config_path}, using defaults")
            # Create default config file
            config.save()
            
        # Load from .env (overrides or supplements)
        config._load_env()

        return config

    def _load_env(self):
        """Load configuration from .env file in project root."""
        import os
        
        # Look for .env in current directory or parent directories
        current = Path.cwd()
        env_path = current / ".env"
        
        # If not in cwd, try to find project root (up to 2 levels)
        if not env_path.exists():
            for _ in range(2):
                current = current.parent
                if (current / ".env").exists():
                    env_path = current / ".env"
                    break
        
        if env_path.exists():
            logger.info(f"Loading environment from {env_path}")
            try:
                with open(env_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip()
                            
                            if key == "DATA_PATH":
                                self.data_path = value
                            elif key == "FORCE_VENV_PATH":
                                # Just for reference, python is already running in venv
                                pass
            except Exception as e:
                logger.warning(f"Failed to parse .env file: {e}")

    def save(self, config_path: Path = None):
        """
        Save configuration to file.

        Args:
            config_path: Path to save to. Uses original load path if not specified.
        """
        if config_path is None:
            config_path = self._config_path

        if config_path is None:
            config_path = Path.home() / ".schmekla" / "config.yaml"

        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            data = self._to_dict()
            with open(config_path, "w") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            logger.debug(f"Configuration saved to {config_path}")
        except Exception as e:
            logger.error(f"Failed to save config to {config_path}: {e}")

    def _to_dict(self) -> dict:
        """Convert config to dictionary for serialization."""
        return {
            "ui": {
                "theme": self.ui.theme,
                "viewport_background": self.ui.viewport_background,
                "grid_visible": self.ui.grid_visible,
                "axes_visible": self.ui.axes_visible,
                "default_dock_layout": self.ui.default_dock_layout,
            },
            "units": {
                "length": self.units.length,
                "angle": self.units.angle,
                "force": self.units.force,
            },
            "export": {
                "ifc_schema": self.export.ifc_schema,
                "ifc_include_grids": self.export.ifc_include_grids,
                "ifc_include_levels": self.export.ifc_include_levels,
                "default_export_dir": self.export.default_export_dir,
            },
            "claude": {
                "enabled": self.claude.enabled,
                "timeout_seconds": self.claude.timeout_seconds,
                "max_history_length": self.claude.max_history_length,
                "auto_execute_commands": self.claude.auto_execute_commands,
            },
            "recent_files": self.recent_files,
            "max_recent_files": self.max_recent_files,
            "profile_catalog_path": self.profile_catalog_path,
            "material_catalog_path": self.material_catalog_path,
            "data_path": self.data_path,
        }

    def _update_from_dict(self, data: dict):
        """Update config from dictionary."""
        if "ui" in data:
            for key, value in data["ui"].items():
                if hasattr(self.ui, key):
                    setattr(self.ui, key, value)

        if "units" in data:
            for key, value in data["units"].items():
                if hasattr(self.units, key):
                    setattr(self.units, key, value)

        if "export" in data:
            for key, value in data["export"].items():
                if hasattr(self.export, key):
                    setattr(self.export, key, value)

        if "claude" in data:
            for key, value in data["claude"].items():
                if hasattr(self.claude, key):
                    setattr(self.claude, key, value)

        if "recent_files" in data:
            self.recent_files = data["recent_files"]

        if "max_recent_files" in data:
            self.max_recent_files = data["max_recent_files"]

        if "profile_catalog_path" in data:
            self.profile_catalog_path = data["profile_catalog_path"]

        if "material_catalog_path" in data:
            self.material_catalog_path = data["material_catalog_path"]

        if "data_path" in data:
            self.data_path = data["data_path"]

    def add_recent_file(self, file_path: str):
        """Add a file to recent files list."""
        # Remove if already exists
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)

        # Add to front
        self.recent_files.insert(0, file_path)

        # Trim to max length
        self.recent_files = self.recent_files[:self.max_recent_files]

        # Save
        self.save()

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key."""
        parts = key.split(".")
        obj = self
        for part in parts:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                return default
        return obj
