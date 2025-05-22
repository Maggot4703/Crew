from pathlib import Path
from typing import Dict, Any
import json
import logging

class Config:
    """Configuration management for Crew Manager"""
    
    DEFAULT_CONFIG = {
        "window_size": "1200x800",
        "min_window_size": "800x600",
        "column_widths": {},
        "last_directory": str(Path.home()),
        "data_dir": "data",
        "log_level": "INFO",
        "auto_save": True
    }

    def __init__(self):
        self.config_dir = Path.home() / ".crewmanager"
        self.config_file = self.config_dir / "config.json"
        self.settings = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
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
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value and save"""
        self.settings[key] = value
        self.save_config()