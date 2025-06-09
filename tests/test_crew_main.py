#!/usr/bin/python3
"""
Test module for main Crew functionality.
"""

import sys
import unittest
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Crew import get_version, main


class TestCrewMainFunctions(unittest.TestCase):
    """Test suite for main Crew.py functions."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.test_csv_path = os.path.join(self.test_dir, "test_npcs.csv")

        test_csv_content = """NAME,ROLE,SQUAD,PRIMUS,SECUNDUS
John Doe,Captain,Alpha,Leadership,Tactics
Jane Smith,Engineer,Beta,Repair,Electronics"""

        with open(self.test_csv_path, "w") as f:
            f.write(test_csv_content)

    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.test_csv_path):
            os.remove(self.test_csv_path)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_hex_to_rgb_conversion(self):
        """Test hex to RGB color conversion."""
        self.assertEqual(Crew.hex_to_rgb("#FF0000"), (255, 0, 0))
        self.assertEqual(Crew.hex_to_rgb("#00FF00"), (0, 255, 0))
        self.assertEqual(Crew.hex_to_rgb("#0000FF"), (0, 0, 255))
        self.assertEqual(Crew.hex_to_rgb("#FFFFFF"), (255, 255, 255))

    def test_rgb_to_hex_conversion(self):
        """Test RGB to hex color conversion."""
        self.assertEqual(Crew.rgb_to_hex((255, 0, 0)), "#FF0000")
        self.assertEqual(Crew.rgb_to_hex((0, 255, 0)), "#00FF00")
        self.assertEqual(Crew.rgb_to_hex((0, 0, 255)), "#0000FF")
        self.assertEqual(Crew.rgb_to_hex((255, 255, 255)), "#FFFFFF")

    def test_calculate_hexagon_points(self):
        """Test hexagon point calculation."""
        center = (100, 100)
        radius = 50
        points = Crew.calculate_hexagon_points(center, radius)

        # Should return 6 points for hexagon
        self.assertEqual(len(points), 6)

        # Each point should be a tuple of 2 coordinates
        for point in points:
            self.assertEqual(len(point), 2)
            self.assertIsInstance(point[0], (int, float))
            self.assertIsInstance(point[1], (int, float))

    def test_read_csv_builtin(self):
        """Test reading CSV with built-in csv module."""
        result = Crew.read_csv_builtin(self.test_csv_path)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

        # Check header row
        header = result[0]
        self.assertIn("NAME", header)
        self.assertIn("ROLE", header)

    def test_read_file_function(self):
        """Test generic file reading function."""
        content = Crew.read_file(self.test_csv_path)

        self.assertIsInstance(content, str)
        self.assertIn("John Doe", content)
        self.assertIn("Captain", content)

    def test_spacer_function(self):
        """Test spacer function runs without error."""
        try:
            Crew.spacer()
        except Exception as e:
            self.fail(f"spacer() function failed: {e}")

    def test_constants_and_configuration(self):
        """Test that required constants are defined."""
        # Test image dimensions
        self.assertEqual(Crew.WIDTH, 1920)
        self.assertEqual(Crew.HEIGHT, 1080)
        self.assertEqual(Crew.IMAGE_DIMENSIONS, (1920, 1080))

        # Test default colors
        self.assertEqual(Crew.DEFAULT_LINE_COLOR, (255, 0, 0))
        self.assertEqual(Crew.DEFAULT_GRID_COLOR, (0, 255, 0))
        self.assertEqual(Crew.DEFAULT_GRID_SIZE, (10, 10))

    def test_directory_constants(self):
        """Test directory path constants."""
        self.assertIsInstance(Crew.INPUT_DIR, Path)
        self.assertIsInstance(Crew.OUTPUT_DIR, Path)
        self.assertIsInstance(Crew.DATA_DIR, Path)

    def test_main_function_structure(self):
        """Test main function exists and has proper structure."""
        self.assertTrue(hasattr(Crew, "main"))
        self.assertTrue(callable(Crew.main))

    def test_image_file_constants(self):
        """Test image file configuration."""
        self.assertIsInstance(Crew.IMAGE_FILES, list)
        self.assertGreater(len(Crew.IMAGE_FILES), 0)

        # All should be PNG files
        for filename in Crew.IMAGE_FILES:
            self.assertTrue(filename.endswith(".png"))


if __name__ == "__main__":
    unittest.main()
