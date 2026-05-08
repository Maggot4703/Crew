"""
Configuration Manager for Crew Management Application
===================================================

Handles application settings, window state persistence, and user preferences.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Import custom errors for proper error handling
try:
    from errors import ConfigError  # Relative import if errors is in the same package
except ImportError:
    # Fallback if errors module not available or not in a package context
    class ConfigError(Exception):
        pass


# Setup logger for this module
logger = logging.getLogger(__name__)


class Config:
    """Configuration management for Crew Manager

    Handles application configuration settings with validation and error handling.

    This module is responsible for loading, accessing, and potentially
    modifying configuration parameters for the application. It reads
    from a configuration file (JSON) and provides validation for settings.
    """

    DEFAULT_CONFIG = {
        "window_size": "800x800",
        "min_window_size": "800x800",
        "column_widths": {},
        "column_visibility": {},
        "scratchpad_text": "",
        "last_directory": str(Path.home()),
        "last_file_path": "",
        "data_dir": "data",
        "log_level": "INFO",
        "auto_save": True,
        "theme": "default",
        "backup_enabled": True,
        "backup_count": 5,
        "tts_enabled": True,
        "tts_settings": {
            "voice": "default",
            "rate": 150,
            "volume": 1.0,
            "language": "en-US",
            "lead_in_seconds": 0.5,
        },
        "stt_settings": {
            "selected_microphone_name": "",
            "selected_microphone_index": -1,
            "energy_threshold": 300,
            "dynamic_energy_threshold": True,
            "pause_threshold": 0.8,
            "non_speaking_duration": 0.5,
            "listen_timeout": 5.0,
            "phrase_time_limit": 8.0,
            "adjust_for_ambient_noise": False,
            "ambient_noise_duration": 0.5,
        },
        "import_timeout": 30,
        "max_file_size": 100,  # MB
    }

    # Configuration validation schema
    VALIDATION_SCHEMA = {
        "window_size": {"type": str, "pattern": r"^\d+x\d+(?:[+-]\d+){0,2}$"},
        "min_window_size": {"type": str, "pattern": r"^\d+x\d+$"},
        "column_widths": {"type": dict},
        "column_visibility": {"type": dict},
        "scratchpad_text": {"type": str},
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
        "tts_settings": {
            "type": dict,
            "schema": {
                "voice": {"type": str},
                "rate": {"type": (int, float), "min": 0.5, "max": 300},
                "volume": {"type": (int, float), "min": 0.0, "max": 1.0},
                "language": {"type": str},
                "lead_in_seconds": {"type": (int, float), "min": 0.0, "max": 3.0},
            },
        },
        "stt_settings": {
            "type": dict,
            "schema": {
                "selected_microphone_name": {"type": str},
                "selected_microphone_index": {"type": int, "min": -1, "max": 256},
                "energy_threshold": {"type": (int, float), "min": 1, "max": 10000},
                "dynamic_energy_threshold": {"type": bool},
                "pause_threshold": {"type": (int, float), "min": 0.1, "max": 5.0},
                "non_speaking_duration": {
                    "type": (int, float),
                    "min": 0.1,
                    "max": 5.0,
                },
                "listen_timeout": {"type": (int, float), "min": 1.0, "max": 60.0},
                "phrase_time_limit": {
                    "type": (int, float),
                    "min": 1.0,
                    "max": 120.0,
                },
                "adjust_for_ambient_noise": {"type": bool},
                "ambient_noise_duration": {
                    "type": (int, float),
                    "min": 0.1,
                    "max": 5.0,
                },
            },
        },
        "import_timeout": {"type": int, "min": 5, "max": 300},
        "max_file_size": {"type": int, "min": 1, "max": 1000},
    }

    def __init__(
        self,
        config_dir: Union[str, Path] = ".",
        config_filename: str = "config.json",
    ):
        """Initialize Config object.

        Args:
            config_dir: Directory where the config file is stored.
            config_filename: Name of the configuration file.
        """
        self.config_dir = Path(config_dir)
        self.config_file_path = self.config_dir / config_filename
        self.config_dir.mkdir(
            parents=True, exist_ok=True
        )  # Ensure config directory exists
        self.config: Dict[str, Any] = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file, or use defaults if file not found/invalid."""
        if not self.config_file_path.exists():
            logger.info(
                f"Configuration file not found at {self.config_file_path}. Using default configuration."
            )
            self.config = self.DEFAULT_CONFIG.copy()
            self.save_config()  # Save defaults if no config file exists
            return self.config

        try:
            with open(self.config_file_path, "r", encoding="utf-8") as f:
                loaded_config = json.load(f)
            # Merge loaded config with defaults to ensure all keys are present
            config = self.DEFAULT_CONFIG.copy()
            config.update(loaded_config)
            return self._validate_config(config)
        except json.JSONDecodeError as e:
            logger.error(
                f"Error decoding JSON from {self.config_file_path}: {e}. Using default configuration."
            )
            return self.DEFAULT_CONFIG.copy()
        except ConfigError as e:
            logger.error(
                f"Configuration validation error: {e}. Using default configuration."
            )
            return self.DEFAULT_CONFIG.copy()
        except Exception as e:
            logger.error(
                f"Unexpected error loading config: {e}. Using default configuration."
            )
            return self.DEFAULT_CONFIG.copy()

    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the loaded configuration against the schema."""
        validated_config = {}
        for key, rules in self.VALIDATION_SCHEMA.items():
            value = config.get(
                key, self.DEFAULT_CONFIG.get(key)
            )  # Fallback to default if key missing in loaded

            # Special handling for nested dict schema (e.g., tts_settings)
            if rules["type"] is dict and "schema" in rules:
                if not isinstance(value, dict):
                    raise ConfigError(
                        f"Invalid type for '{key}'. Expected dict, got {type(value)}."
                    )
                sub_schema = rules["schema"]
                validated_sub = {}
                for sub_key, sub_rules in sub_schema.items():
                    sub_value = value.get(
                        sub_key, self.DEFAULT_CONFIG[key].get(sub_key)
                    )
                    if not isinstance(sub_value, sub_rules["type"]):
                        raise ConfigError(
                            f"Invalid type for '{key}.{sub_key}'. Expected {sub_rules['type']}, got {type(sub_value)}."
                        )
                    if "min" in sub_rules and sub_value < sub_rules["min"]:
                        raise ConfigError(
                            f"Value for '{key}.{sub_key}' ('{sub_value}') is less than minimum allowed ('{sub_rules['min']}')."
                        )
                    if "max" in sub_rules and sub_value > sub_rules["max"]:
                        raise ConfigError(
                            f"Value for '{key}.{sub_key}' ('{sub_value}') is greater than maximum allowed ('{sub_rules['max']}')."
                        )
                    validated_sub[sub_key] = sub_value
                validated_config[key] = validated_sub
                continue

            if not isinstance(value, rules["type"]):
                raise ConfigError(
                    f"Invalid type for '{key}'. Expected {rules['type']}, got {type(value)}."
                )

            if "pattern" in rules and not re.match(rules["pattern"], value):
                raise ConfigError(
                    f"Invalid format for '{key}'. Value '{value}' does not match pattern '{rules['pattern']}'."
                )

            if "choices" in rules and value not in rules["choices"]:
                raise ConfigError(
                    f"Invalid value for '{key}'. '{value}' is not in {rules['choices']}."
                )

            if "min" in rules and value < rules["min"]:
                raise ConfigError(
                    f"Value for '{key}' ('{value}') is less than minimum allowed ('{rules['min']}')."
                )

            if "max" in rules and value > rules["max"]:
                raise ConfigError(
                    f"Value for '{key}' ('{value}') is greater than maximum allowed ('{rules['max']}')."
                )

            validated_config[key] = value

        # Check for unknown keys (optional, could be logged as warning)
        for key in config:
            if key not in self.VALIDATION_SCHEMA:
                logger.warning(
                    f"Unknown configuration key '{key}' found in config file."
                )
                # Decide whether to include them or not. For now, we'll include them.
                validated_config[key] = config[key]

        return validated_config

    def save_config(self) -> None:
        """Save the current configuration to the file."""
        try:
            self._save_to_file(self.config, self.config_file_path)
            logger.info(f"Configuration saved to {self.config_file_path}")
        except Exception as e:
            logger.error(
                f"Error saving configuration to {self.config_file_path}: {e}",
                exc_info=True,
            )
            # Optionally raise a ConfigError here if saving is critical

    def _save_to_file(self, config: Dict[str, Any], file_path: Path) -> None:
        """Helper to save dictionary to a JSON file."""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key.

        Args:
            key: The configuration key.
            default: Default value if key is not found.

        Returns:
            The configuration value or default.
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value and save the configuration.

        Args:
            key: The configuration key.
            value: The value to set.
        """
        if key not in self.VALIDATION_SCHEMA:
            logger.warning(
                f"Attempting to set an unknown configuration key: '{key}'. This key is not validated."
            )
        else:
            # Basic validation before setting (more thorough in _validate_config)
            rules = self.VALIDATION_SCHEMA[key]
            if not isinstance(value, rules["type"]):
                logger.error(
                    f"Cannot set '{key}': Invalid type. Expected {rules['type']}, got {type(value)}."
                )
                # Or raise ConfigError("Invalid type...")
                return
            # Add other quick checks from VALIDATION_SCHEMA if desired before full save/validate cycle

        self.config[key] = value
        self.save_config()  # Save after every set operation
        # Reload and re-validate after save to ensure integrity, or trust the set operation.
        # For simplicity, we are not re-validating the entire config on each set here,
        # but it might be safer in complex scenarios.

    def reset_to_defaults(self) -> None:
        """Reset the configuration to default values and save."""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save_config()
        logger.info("Configuration has been reset to defaults.")

    def get_window_geometry(self) -> Optional[tuple[int, int, int, int]]:
        """Parse window_size and return as (width, height, x_offset, y_offset)."""
        size_str = self.get("window_size")
        if size_str and isinstance(size_str, str) and "x" in size_str:
            try:
                match = re.fullmatch(r"(\d+)x(\d+)([+-]\d+)?([+-]\d+)?", size_str)
                if not match:
                    raise ValueError(size_str)
                width = int(match.group(1))
                height = int(match.group(2))
                x_offset = int(match.group(3) or 0)
                y_offset = int(match.group(4) or 0)
                return width, height, x_offset, y_offset
            except ValueError:
                logger.error(
                    f"Invalid window_size format: '{size_str}'. Expected 'WIDTHxHEIGHT' or 'WIDTHxHEIGHT+X+Y'."
                )
                return None
        return None


# Example usage (optional, for testing or direct script run)
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    config_manager = Config(config_dir=".config_test")  # Use a test directory
    print(f"Loaded config: {config_manager.config}")

    print(f"Window size: {config_manager.get('window_size')}")
    config_manager.set("log_level", "DEBUG")
    print(f"Log level after set: {config_manager.get('log_level')}")

    # Test validation failure (example)
    # config_manager.set("backup_count", 999) # This should log an error if validation on set is more robust or fail on next load

    geom = config_manager.get_window_geometry()
    if geom:
        print(f"Window geometry: width={geom[0]}, height={geom[1]}")

    config_manager.reset_to_defaults()
    print(f"Config after reset: {config_manager.config}")

    # Clean up test config file
    # import shutil
    # shutil.rmtree(".config_test", ignore_errors=True)
