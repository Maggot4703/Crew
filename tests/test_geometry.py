"""Tests for geometric and color calculations in Crew.py"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Crew import calculate_hexagon_points, hex_to_rgb, rgb_to_hex


class TestGeometricCalculations(unittest.TestCase):
    """Test suite for geometric and color calculation functions."""

    def test_hex_to_rgb_with_hash(self):
        """Test hex_to_rgb with hash prefix."""
        result = hex_to_rgb("#FF5733")
        expected = (255, 87, 51)
        self.assertEqual(result, expected)

    def test_rgb_to_hex(self):
        """Test rgb_to_hex function."""
        result = rgb_to_hex((255, 87, 51))
        expected = "#FF5733"
        self.assertEqual(result, expected)

    def test_calculate_hexagon_points_default(self):
        """Test calculate_hexagon_points with default center."""
        points = calculate_hexagon_points(100)
        self.assertEqual(len(points), 6)

    def test_calculate_hexagon_points_zero_height(self):
        """Test calculate_hexagon_points with zero height."""
        points = calculate_hexagon_points(0)
        self.assertEqual(points, [])


if __name__ == "__main__":
    unittest.main()
