#!/usr/bin/python3
"""
Test module for configuration functionality.
"""

import sys
import unittest
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))



# Import Config from config.py
from config import Config

# Import patch for mocking
from unittest.mock import patch


class TestConfig(unittest.TestCase):
    """Test suite for Config class functionality."""

    def setUp(self):
        """Set up test environment before each test."""
        import tempfile
        self.tempfile = tempfile
        self.test_dir = self.tempfile.mkdtemp()
        self.config_path = Path(self.test_dir) / "config.json"

    def tearDown(self):
        """Clean up test environment after each test."""
        import shutil
        if self.test_dir and Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_config_initialization(self):
        """Test Config class initialization with default values."""
        config = Config(config_dir=self.test_dir)
        self.assertIsInstance(config, Config)
        self.assertIn("window_size", config.DEFAULT_CONFIG)
        self.assertEqual(config.DEFAULT_CONFIG["window_size"], "800x800")

    def test_default_config_values(self):
        """Test that default configuration contains expected values."""
        config = Config(config_dir=self.test_dir)
        defaults = config.DEFAULT_CONFIG

        # Test key default values
        self.assertEqual(defaults["window_size"], "800x800")
        self.assertEqual(defaults["min_window_size"], "800x800")
        self.assertEqual(defaults["data_dir"], "data")
        self.assertEqual(defaults["log_level"], "INFO")
        self.assertTrue(defaults["auto_save"])
        self.assertIsInstance(defaults["column_widths"], dict)

    def test_get_default_value(self):
        """Test getting configuration values with defaults."""
        config = Config(config_dir=self.test_dir)
        # Test getting existing default value
        result = config.get("window_size")
        self.assertEqual(result, "800x800")

        # Test getting non-existent value with default
        result = config.get("non_existent_key", "default_value")
        self.assertEqual(result, "default_value")

    def test_set_and_get_value(self):
        """Test setting and getting configuration values."""
        config = Config(config_dir=self.test_dir)

        # Test setting new value
        config.set("test_key", "test_value")
        result = config.get("test_key")
        self.assertEqual(result, "test_value")

        # Test overriding existing value
        config.set("window_size", "1600x900")
        result = config.get("window_size")
        self.assertEqual(result, "1600x900")

    def test_column_widths_management(self):
        """Test column widths configuration management."""
        config = Config(config_dir=self.test_dir)

        # Test setting column widths
        test_widths = {"col1": 100, "col2": 150, "col3": 200}
        config.set("column_widths", test_widths)

        result = config.get("column_widths")
        self.assertEqual(result, test_widths)

    def test_config_data_types(self):
        """Test configuration with different data types."""
        config = Config(config_dir=self.test_dir)

        # Test string value
        config.set("string_val", "test")
        self.assertEqual(config.get("string_val"), "test")

        # Test integer value
        config.set("int_val", 42)
        self.assertEqual(config.get("int_val"), 42)

        # Test boolean value
        config.set("bool_val", False)
        self.assertEqual(config.get("bool_val"), False)

        # Test list value
        config.set("list_val", [1, 2, 3])
        self.assertEqual(config.get("list_val"), [1, 2, 3])

    def test_auto_save_default(self):
        """Test auto-save configuration default."""
        config = Config(config_dir=self.test_dir)
        auto_save = config.get("auto_save")
        self.assertTrue(auto_save)
        self.assertIsInstance(auto_save, bool)

    def test_log_level_default(self):
        """Test log level configuration default."""
        config = Config(config_dir=self.test_dir)
        log_level = config.get("log_level")
        self.assertEqual(log_level, "INFO")


if __name__ == "__main__":
    unittest.main()
