"""
Test suite for the errors module.

This module tests custom exception classes and error handling functionality.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from errors import (
    CacheError,
    ConfigError,
    CrewManagerError,
    DatabaseError,
    FileOperationError,
    GUIError,
    ScraperError,
)


class TestErrorClasses(unittest.TestCase):
    """Test suite for custom error classes."""

    def test_crew_manager_error_base_class(self):
        """Test CrewManagerError base exception class."""
        error = CrewManagerError("Test error message")
        self.assertIsInstance(error, Exception)
        self.assertIsInstance(error, CrewManagerError)
        self.assertEqual(str(error), "Test error message")

    def test_database_error_inheritance(self):
        """Test DatabaseError inherits from CrewManagerError."""
        error = DatabaseError("Database connection failed")
        self.assertIsInstance(error, CrewManagerError)
        self.assertIsInstance(error, DatabaseError)
        self.assertEqual(str(error), "Database connection failed")

    def test_config_error_inheritance(self):
        """Test ConfigError inherits from CrewManagerError."""
        error = ConfigError("Configuration file not found")
        self.assertIsInstance(error, CrewManagerError)
        self.assertIsInstance(error, ConfigError)

    def test_cache_error_inheritance(self):
        """Test CacheError inherits from CrewManagerError."""
        error = CacheError("Cache invalidation failed")
        self.assertIsInstance(error, CrewManagerError)
        self.assertIsInstance(error, CacheError)

    def test_gui_error_inheritance(self):
        """Test GUIError inherits from CrewManagerError."""
        error = GUIError("GUI initialization failed")
        self.assertIsInstance(error, CrewManagerError)
        self.assertIsInstance(error, GUIError)

    def test_error_raising_and_catching(self):
        """Test raising and catching custom errors."""
        with self.assertRaises(DatabaseError):
            raise DatabaseError("Test database error")

        with self.assertRaises(ConfigError):
            raise ConfigError("Test config error")

        with self.assertRaises(GUIError):
            raise GUIError("Test GUI error")

    def test_catch_base_error(self):
        """Test catching errors using base CrewManagerError class."""
        errors_to_test = [
            DatabaseError("DB error"),
            ConfigError("Config error"),
            GUIError("GUI error"),
        ]

        for error in errors_to_test:
            with self.assertRaises(CrewManagerError):
                raise error

    def test_error_with_empty_message(self):
        """Test error classes with empty messages."""
        error = CrewManagerError("")
        self.assertEqual(str(error), "")

        db_error = DatabaseError("")
        self.assertEqual(str(db_error), "")

    def test_error_class_docstrings(self):
        """Test that error classes have appropriate docstrings."""
        self.assertIsNotNone(CrewManagerError.__doc__)
        self.assertIsNotNone(DatabaseError.__doc__)
        self.assertIsNotNone(ConfigError.__doc__)


if __name__ == "__main__":
    unittest.main()
