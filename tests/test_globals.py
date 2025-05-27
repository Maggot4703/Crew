"""
Test suite for globals.py module.

This module tests the global constants, variables, and utility classes
defined in the globals module.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import globals


class TestGlobals(unittest.TestCase):
    """Test suite for globals module."""

    def test_application_constants(self):
        """Test application-level constants."""
        self.assertEqual(globals.APP_VERSION, "1.0.0")
        self.assertEqual(globals.APP_NAME, "Crew Management System")
        self.assertIsInstance(globals.DEBUG_MODE, bool)

    def test_ui_constants(self):
        """Test UI-related constants."""
        self.assertEqual(globals.DEFAULT_THEME, "light")
        self.assertEqual(globals.MAX_TABLE_ROWS, 100)
        self.assertIsInstance(globals.MAX_TABLE_ROWS, int)

    def test_path_constants(self):
        """Test path-related constants."""
        self.assertIsInstance(globals.paths, tuple)
        self.assertEqual(len(globals.paths), 4)

        # Test individual path components
        self.assertEqual(globals.CALC, "/usr/bin/galculator")
        self.assertEqual(globals.FF, "/usr/bin/firefox")
        self.assertEqual(globals.ED, "/usr/bin/geany")
        self.assertEqual(globals.HOME, "/home/me")

    def test_math_constants(self):
        """Test mathematical operation constants."""
        self.assertIsInstance(globals.math, tuple)
        self.assertEqual(len(globals.math), 6)

        # Test individual math operators
        self.assertEqual(globals.PLUS, "+")
        self.assertEqual(globals.MINUS, "-")
        self.assertEqual(globals.MULT, "*")
        self.assertEqual(globals.DIV, "/")
        self.assertEqual(globals.EQUAL, "=")
        self.assertEqual(globals.MOD, "%")

    def test_vehicle_constants(self):
        """Test vehicle type constants."""
        self.assertIsInstance(globals.vehicles, tuple)

        # Test individual vehicle types
        self.assertEqual(globals.MAN, "Man")
        self.assertEqual(globals.BIKE, "Bike")
        self.assertEqual(globals.CAR, "Car")
        self.assertEqual(globals.TRUCK, "Truck")


if __name__ == "__main__":
    unittest.main()
