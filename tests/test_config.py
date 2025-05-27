#!/usr/bin/python3
"""
Test module for configuration functionality.
"""

import sys
import unittest
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Crew import get_version


class TestConfig(unittest.TestCase):
    """Test suite for Config class functionality."""

    def setUp(self):
        """Set up test environment before each test."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test environment after each test."""
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_config_initialization(self):
        """Test Config class initialization with default values."""
        config = Config()
        self.assertIsInstance(config, Config)
        self.assertIn("window_size", config.DEFAULT_CONFIG)
        self.assertEqual(config.DEFAULT_CONFIG["window_size"], "1200x800")

    def test_default_config_values(self):
        """Test that default configuration contains expected values."""
        config = Config()
        defaults = config.DEFAULT_CONFIG

        # Test key default values
        self.assertEqual(defaults["window_size"], "1200x800")
        self.assertEqual(defaults["min_window_size"], "800x600")
        self.assertEqual(defaults["data_dir"], "data")
        self.assertEqual(defaults["log_level"], "INFO")
        self.assertTrue(defaults["auto_save"])
        self.assertIsInstance(defaults["column_widths"], dict)

    def test_get_default_value(self):
        """Test getting configuration values with defaults."""
        # Create config with isolated test directory
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("config.Path.home", return_value=Path(temp_dir)):
                config = Config()

                # Test getting existing default value
                result = config.get("window_size")
                self.assertEqual(result, "1200x800")

                # Test getting non-existent value with default
                result = config.get("non_existent_key", "default_value")
                self.assertEqual(result, "default_value")

    def test_set_and_get_value(self):
        """Test setting and getting configuration values."""
        config = Config()

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
        config = Config()

        # Test setting column widths
        test_widths = {"col1": 100, "col2": 150, "col3": 200}
        config.set("column_widths", test_widths)

        result = config.get("column_widths")
        self.assertEqual(result, test_widths)

    def test_config_data_types(self):
        """Test configuration with different data types."""
        config = Config()

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
        config = Config()
        auto_save = config.get("auto_save")
        self.assertTrue(auto_save)
        self.assertIsInstance(auto_save, bool)

    def test_log_level_default(self):
        """Test log level configuration default."""
        config = Config()
        log_level = config.get("log_level")
        self.assertEqual(log_level, "INFO")


if __name__ == "__main__":
    unittest.main()
