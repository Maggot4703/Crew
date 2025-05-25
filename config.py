import json
import logging
from pathlib import Path
from typing import Any, Dict


class Config:
    """Configuration management for Crew Manager

    Handles application configuration settings.

    This module is responsible for loading, accessing, and potentially
    modifying configuration parameters for the application. It might read
    from a configuration file (e.g., INI, YAML, JSON) or environment variables.
    """

    DEFAULT_CONFIG = {
        "window_size": "1200x800",
        "min_window_size": "800x600",
        "column_widths": {},
        "last_directory": str(Path.home()),
        "data_dir": "data",
        "log_level": "INFO",
        "auto_save": True,
    }

    def __init__(self):
        self.config_dir = Path.home() / ".crewmanager"
        self.config_file = self.config_dir / "config.json"
        self.settings = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file

        Parses the configuration file and returns a dictionary of settings.
        Handles potential errors like file not found or parsing issues.

        Returns:
            dict: A dictionary containing the configuration settings.
        """
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            if self.config_file.exists():
                with open(self.config_file) as f:
                    return {**self.DEFAULT_CONFIG, **json.load(f)}
            return dict(self.DEFAULT_CONFIG)
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            return dict(self.DEFAULT_CONFIG)

    def save_config(self) -> None:
        """Save configuration to file

        Saves the current configuration settings to the config file.

        Returns:
            None
        """
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value

        Retrieve a specific setting by its key.

        Args:
            key (str): The key of the setting to retrieve.
            default (any, optional): The value to return if the key is not found.
                                    Defaults to None.

        Returns:
            any: The value of the setting, or the default value if not found.
        """
        return self.settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value and save

        Updates a configuration setting and immediately saves the changes to the file.

        Args:
            key (str): The key of the setting to update.
            value (Any): The new value for the setting.

        Returns:
            None
        """
        self.settings[key] = value
        self.save_config()
