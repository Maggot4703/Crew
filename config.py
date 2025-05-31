"""
Configuration Manager for Crew Management Application
===================================================

Handles application settings, window state persistence, and user preferences.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Union

# Import custom errors for proper error handling
try:
    from errors import ConfigError
except ImportError:
    # Fallback if errors module not available
    class ConfigError(Exception):
        pass


class Config:
    """Configuration management for Crew Manager

    Handles application configuration settings with validation and error handling.

    This module is responsible for loading, accessing, and potentially
    modifying configuration parameters for the application. It reads
    from a configuration file (JSON) and provides validation for settings.
    """

    DEFAULT_CONFIG = {
        "window_size": "1200x800",
        "min_window_size": "800x600",
        "column_widths": {},
        "column_visibility": {},
        "last_directory": str(Path.home()),
        "last_file_path": "",
        "data_dir": "data",
        "log_level": "INFO",
        "auto_save": True,
        "theme": "default",
        "backup_enabled": True,
        "backup_count": 5,
        "tts_enabled": True,
        "import_timeout": 30,
        "max_file_size": 100,  # MB
    }

    # Configuration validation schema
    VALIDATION_SCHEMA = {
        "window_size": {"type": str, "pattern": r"^\d+x\d+$"},
        "min_window_size": {"type": str, "pattern": r"^\d+x\d+$"},
        "column_widths": {"type": dict},
        "column_visibility": {"type": dict},
        "last_directory": {"type": str},
        "last_file_path": {"type": str},
        "data_dir": {"type": str},
        "log_level": {
            "type": str,
            "choices": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        },
        "auto_save": {"type": bool},
        "theme": {"type": str, "choices": ["default", "dark", "light"]},
        "backup_enabled": {"type": bool},
        "backup_count": {"type": int, "min": 1, "max": 50},
        "tts_enabled": {"type": bool},
        "import_timeout": {"type": int, "min": 5, "max": 300},
        "max_file_size": {"type": int, "min": 1, "max": 1000},
    }

    def __init__(self, config_dir: Union[str, Path] = None):
        """Initialize configuration manager.

        Args:
            config_dir: Custom configuration directory path. Defaults to ~/.crewmanager
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / ".crewmanager"

        self.config_file = self.config_dir / "config.json"
        self.backup_file = self.config_dir / "config.backup.json"
        self.logger = logging.getLogger(__name__)

        # Load configuration with error handling
        self.settings = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file with comprehensive error handling.

        Attempts to load configuration from the config file, with fallback
        to backup file if the main config is corrupted. If both fail,
        uses default configuration.

        Returns:
            dict: A dictionary containing the configuration settings.

        Raises:
            ConfigError: If configuration validation fails.
        """
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # Try to load main config file
            if self.config_file.exists():
                try:
                    with open(self.config_file, "r", encoding="utf-8") as f:
                        loaded_config = json.load(f)

                    # Merge with defaults and validate
                    merged_config = {**self.DEFAULT_CONFIG, **loaded_config}
                    validated_config = self._validate_config(merged_config)

                    self.logger.info("Configuration loaded successfully")
                    return validated_config

                except (json.JSONDecodeError, KeyError) as e:
                    self.logger.warning(f"Main config file corrupted: {e}")
                    # Try backup file
                    if self.backup_file.exists():
                        try:
                            with open(self.backup_file, "r", encoding="utf-8") as f:
                                backup_config = json.load(f)

                            merged_config = {**self.DEFAULT_CONFIG, **backup_config}
                            validated_config = self._validate_config(merged_config)

                            self.logger.info("Configuration restored from backup")
                            # Save the restored config as main config
                            self._save_to_file(validated_config, self.config_file)
                            return validated_config

                        except Exception as backup_error:
                            self.logger.error(
                                f"Backup config also corrupted: {backup_error}"
                            )

            # Use default configuration if no valid config found
            self.logger.info("Using default configuration")
            default_config = dict(self.DEFAULT_CONFIG)
            self._save_to_file(default_config, self.config_file)
            return default_config

        except Exception as e:
            self.logger.error(f"Critical error loading config: {e}")
            # Return defaults as last resort
            return dict(self.DEFAULT_CONFIG)

    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration against schema.

        Args:
            config: Configuration dictionary to validate

        Returns:
            dict: Validated configuration dictionary

        Raises:
            ConfigError: If validation fails
        """
        import re

        validated = {}

        for key, value in config.items():
            if key not in self.VALIDATION_SCHEMA:
                self.logger.warning(f"Unknown config key: {key}")
                continue

            schema = self.VALIDATION_SCHEMA[key]

            # Type validation
            expected_type = schema["type"]
            if not isinstance(value, expected_type):
                try:
                    # Try to convert basic types
                    if expected_type == int:
                        value = int(value)
                    elif expected_type == bool:
                        if isinstance(value, str):
                            value = value.lower() in ("true", "1", "yes", "on")
                        else:
                            value = bool(value)
                    elif expected_type == str:
                        value = str(value)
                except (ValueError, TypeError):
                    self.logger.warning(
                        f"Invalid type for {key}: {type(value).__name__}, expected {expected_type.__name__}"
                    )
                    value = self.DEFAULT_CONFIG[key]

            # Pattern validation for strings
            if "pattern" in schema and isinstance(value, str):
                if not re.match(schema["pattern"], value):
                    self.logger.warning(f"Invalid pattern for {key}: {value}")
                    value = self.DEFAULT_CONFIG[key]

            # Choice validation
            if "choices" in schema and value not in schema["choices"]:
                self.logger.warning(f"Invalid choice for {key}: {value}")
                value = self.DEFAULT_CONFIG[key]

            # Range validation for integers
            if expected_type == int:
                if "min" in schema and value < schema["min"]:
                    self.logger.warning(f"Value for {key} below minimum: {value}")
                    value = schema["min"]
                if "max" in schema and value > schema["max"]:
                    self.logger.warning(f"Value for {key} above maximum: {value}")
                    value = schema["max"]

            validated[key] = value

        # Ensure all required keys are present
        for key in self.DEFAULT_CONFIG:
            if key not in validated:
                validated[key] = self.DEFAULT_CONFIG[key]

        return validated

    def save_config(self) -> None:
        """Save configuration to file with backup.

        Creates a backup of the current config before saving the new one.
        This ensures we always have a fallback if the save operation corrupts the file.

        Raises:
            ConfigError: If saving fails
        """
        try:
            # Validate before saving
            validated_settings = self._validate_config(self.settings)

            # Create backup of current config if it exists
            if self.config_file.exists():
                try:
                    import shutil

                    shutil.copy2(self.config_file, self.backup_file)
                except Exception as e:
                    self.logger.warning(f"Could not create config backup: {e}")

            # Save new config
            self._save_to_file(validated_settings, self.config_file)
            self.settings = validated_settings
            self.logger.debug("Configuration saved successfully")

        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
            raise ConfigError(f"Failed to save configuration: {e}")

    def _save_to_file(self, config: Dict[str, Any], file_path: Path) -> None:
        """Save configuration dictionary to file.

        Args:
            config: Configuration to save
            file_path: Path to save to
        """
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with validation.

        Retrieve a specific setting by its key with optional default value.

        Args:
            key (str): The key of the setting to retrieve.
            default (any, optional): The value to return if the key is not found.
                                    If None, uses the default from DEFAULT_CONFIG.

        Returns:
            any: The value of the setting, or the default value if not found.
        """
        if default is None and key in self.DEFAULT_CONFIG:
            default = self.DEFAULT_CONFIG[key]

        value = self.settings.get(key, default)

        # Re-validate single values that might have been manually modified
        if key in self.VALIDATION_SCHEMA:
            try:
                temp_config = {key: value}
                validated = self._validate_config(temp_config)
                return validated[key]
            except Exception:
                self.logger.warning(f"Validation failed for {key}, returning default")
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value with validation and immediate save.

        Updates a configuration setting, validates it, and immediately saves
        the changes to the file.

        Args:
            key (str): The key of the setting to update.
            value (Any): The new value for the setting.

        Raises:
            ConfigError: If the value fails validation
        """
        # Validate the new value
        if key in self.VALIDATION_SCHEMA:
            temp_config = {**self.settings, key: value}
            try:
                validated_config = self._validate_config(temp_config)
                validated_value = validated_config[key]
            except Exception as e:
                raise ConfigError(f"Invalid value for {key}: {e}")
        else:
            validated_value = value
            self.logger.warning(f"Setting unknown config key: {key}")

        self.settings[key] = validated_value
        self.save_config()

    def reset_to_defaults(self) -> None:
        """Reset configuration to default values.

        Resets all settings to their default values and saves the configuration.
        """
        self.logger.info("Resetting configuration to defaults")
        self.settings = dict(self.DEFAULT_CONFIG)
        self.save_config()

    def get_window_geometry(self) -> tuple:
        """Get window geometry as (width, height) tuple.

        Returns:
            tuple: (width, height) as integers
        """
        size_str = self.get("window_size", "1200x800")
        try:
            width, height = map(int, size_str.split("x"))
            return (width, height)
        except ValueError:
            self.logger.warning(f"Invalid window size format: {size_str}")
            return (1200, 800)

    def set_window_geometry(self, width: int, height: int) -> None:
        """Set window geometry from width and height values.

        Args:
            width: Window width in pixels
            height: Window height in pixels
        """
        if width < 400:
            width = 400
        if height < 300:
            height = 300

        self.set("window_size", f"{width}x{height}")

    def get_config_info(self) -> Dict[str, Any]:
        """Get information about the configuration system.

        Returns:
            dict: Information about config file paths, validation status, etc.
        """
        return {
            "config_file": str(self.config_file),
            "backup_file": str(self.backup_file),
            "config_exists": self.config_file.exists(),
            "backup_exists": self.backup_file.exists(),
            "config_dir": str(self.config_dir),
            "settings_count": len(self.settings),
            "schema_keys": list(self.VALIDATION_SCHEMA.keys()),
        }

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration settings."""
        return dict(self.DEFAULT_CONFIG)
