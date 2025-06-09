"""
Tests for image processing utilities in Crew.py
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

# Add parent directory to path to import Crew module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Crew import (
    DEFAULT_GRID_COLOR,
    DEFAULT_GRID_SIZE,
    DEFAULT_LINE_COLOR,
    IMAGE_DIMENSIONS,
    markHorizontalLine,
    overlayGrid,
)


class TestImageProcessing(unittest.TestCase):
    """Test suite for image processing functions."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_image_path = os.path.join(self.temp_dir, "test_image.png")

        # Create a simple test image
        test_img = Image.new("RGB", (200, 100), "white")
        test_img.save(self.test_image_path)

        # Create a larger test image for grid testing
        self.large_image_path = os.path.join(self.temp_dir, "large_test_image.png")
        large_img = Image.new("RGB", (400, 300), "white")
        large_img.save(self.large_image_path)

    def tearDown(self):
        """Clean up test fixtures after each test method."""
        if os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)
        if os.path.exists(self.large_image_path):
            os.remove(self.large_image_path)
        os.rmdir(self.temp_dir)

    # region markHorizontalLine Tests
    def test_markHorizontalLine_default_parameters(self):
        """Test markHorizontalLine with default parameters."""
        img = markHorizontalLine(10, 10, 100, 10)
        self.assertEqual(img.size, IMAGE_DIMENSIONS)
        self.assertEqual(img.mode, "RGB")
        self.assertIsNotNone(img)

    def test_markHorizontalLine_custom_color(self):
        """Test markHorizontalLine with custom color."""
        custom_color = (0, 255, 255)  # Cyan
        img = markHorizontalLine(0, 50, 100, 50, color=custom_color)
        self.assertEqual(img.size, IMAGE_DIMENSIONS)
        self.assertEqual(img.mode, "RGB")

        # Check that the line was drawn by examining a pixel
        pixel_color = img.getpixel((50, 50))
        self.assertEqual(pixel_color, custom_color)

    def test_markHorizontalLine_custom_thickness(self):
        """Test markHorizontalLine with custom thickness."""
        img = markHorizontalLine(10, 10, 100, 10, thickness=5)
        self.assertEqual(img.size, IMAGE_DIMENSIONS)
        self.assertEqual(img.mode, "RGB")

    def test_markHorizontalLine_diagonal_line(self):
        """Test markHorizontalLine with diagonal line coordinates."""
        img = markHorizontalLine(0, 0, 100, 100)
        self.assertEqual(img.size, IMAGE_DIMENSIONS)
        self.assertEqual(img.mode, "RGB")

    def test_markHorizontalLine_vertical_line(self):
        """Test markHorizontalLine with vertical line coordinates."""
        img = markHorizontalLine(50, 0, 50, 100)
        self.assertEqual(img.size, IMAGE_DIMENSIONS)
        self.assertEqual(img.mode, "RGB")

    def test_markHorizontalLine_zero_length_line(self):
        """Test markHorizontalLine with zero-length line (point)."""
        img = markHorizontalLine(50, 50, 50, 50)
        self.assertEqual(img.size, IMAGE_DIMENSIONS)
        self.assertEqual(img.mode, "RGB")

    def test_markHorizontalLine_negative_coordinates(self):
        """Test markHorizontalLine with negative coordinates."""
        img = markHorizontalLine(-10, -10, 50, 50)
        self.assertEqual(img.size, IMAGE_DIMENSIONS)
        self.assertEqual(img.mode, "RGB")

    def test_markHorizontalLine_coordinates_outside_image(self):
        """Test markHorizontalLine with coordinates outside image bounds."""
        img = markHorizontalLine(
            0, 0, IMAGE_DIMENSIONS[0] + 100, IMAGE_DIMENSIONS[1] + 100
        )
        self.assertEqual(img.size, IMAGE_DIMENSIONS)
        self.assertEqual(img.mode, "RGB")

    # endregion

    # region overlayGrid Tests
    def test_overlayGrid_valid_image(self):
        """Test overlayGrid with a valid image file."""
        result_img = overlayGrid(self.test_image_path)
        self.assertIsInstance(result_img, Image.Image)
        # Original image size should be preserved
        self.assertEqual(result_img.size, (200, 100))

    def test_overlayGrid_invalid_file(self):
        """Test overlayGrid with non-existent file."""
        with self.assertRaises(FileNotFoundError):
            overlayGrid("nonexistent_file.png")

    def test_overlayGrid_invalid_grid_dimensions(self):
        """Test overlayGrid with invalid grid dimensions."""
        with self.assertRaises(ValueError):
            overlayGrid(self.test_image_path, grid_size=(0, 5))

        with self.assertRaises(ValueError):
            overlayGrid(self.test_image_path, grid_size=(5, 0))

        with self.assertRaises(ValueError):
            overlayGrid(self.test_image_path, grid_size=(-1, 5))

    def test_overlayGrid_custom_color(self):
        """Test overlayGrid with custom grid color."""
        custom_color = (255, 0, 255)  # Magenta
        result_img = overlayGrid(self.test_image_path, grid_color=custom_color)
        self.assertIsInstance(result_img, Image.Image)
        self.assertEqual(result_img.size, (200, 100))

    def test_overlayGrid_custom_grid_size(self):
        """Test overlayGrid with custom grid size."""
        result_img = overlayGrid(self.test_image_path, grid_size=(5, 3))
        self.assertIsInstance(result_img, Image.Image)
        self.assertEqual(result_img.size, (200, 100))

    def test_overlayGrid_single_cell(self):
        """Test overlayGrid with single cell (1x1 grid)."""
        result_img = overlayGrid(self.test_image_path, grid_size=(1, 1))
        self.assertIsInstance(result_img, Image.Image)
        self.assertEqual(result_img.size, (200, 100))

    def test_overlayGrid_large_grid(self):
        """Test overlayGrid with large grid dimensions."""
        result_img = overlayGrid(self.large_image_path, grid_size=(20, 15))
        self.assertIsInstance(result_img, Image.Image)
        self.assertEqual(result_img.size, (400, 300))

    def test_overlayGrid_default_parameters(self):
        """Test overlayGrid with all default parameters."""
        result_img = overlayGrid(self.test_image_path)
        self.assertIsInstance(result_img, Image.Image)
        self.assertEqual(result_img.size, (200, 100))

    def test_overlayGrid_rectangular_grid(self):
        """Test overlayGrid with rectangular (non-square) grid."""
        result_img = overlayGrid(self.test_image_path, grid_size=(4, 2))
        self.assertIsInstance(result_img, Image.Image)
        self.assertEqual(result_img.size, (200, 100))

    def test_overlayGrid_very_fine_grid(self):
        """Test overlayGrid with very fine grid (many small cells)."""
        result_img = overlayGrid(self.large_image_path, grid_size=(50, 30))
        self.assertIsInstance(result_img, Image.Image)
        self.assertEqual(result_img.size, (400, 300))

    # endregion

    # region Constants and Integration Tests
    def test_constants_values(self):
        """Test that constants have expected values and types."""
        # Test IMAGE_DIMENSIONS
        self.assertIsInstance(IMAGE_DIMENSIONS, tuple)
        self.assertEqual(len(IMAGE_DIMENSIONS), 2)
        self.assertIsInstance(IMAGE_DIMENSIONS[0], int)
        self.assertIsInstance(IMAGE_DIMENSIONS[1], int)
        self.assertGreater(IMAGE_DIMENSIONS[0], 0)
        self.assertGreater(IMAGE_DIMENSIONS[1], 0)

        # Test DEFAULT_LINE_COLOR
        self.assertIsInstance(DEFAULT_LINE_COLOR, tuple)
        self.assertEqual(len(DEFAULT_LINE_COLOR), 3)
        for color_value in DEFAULT_LINE_COLOR:
            self.assertIsInstance(color_value, int)
            self.assertGreaterEqual(color_value, 0)
            self.assertLessEqual(color_value, 255)

        # Test DEFAULT_GRID_COLOR
        self.assertIsInstance(DEFAULT_GRID_COLOR, tuple)
        self.assertEqual(len(DEFAULT_GRID_COLOR), 3)
        for color_value in DEFAULT_GRID_COLOR:
            self.assertIsInstance(color_value, int)
            self.assertGreaterEqual(color_value, 0)
            self.assertLessEqual(color_value, 255)

        # Test DEFAULT_GRID_SIZE
        self.assertIsInstance(DEFAULT_GRID_SIZE, tuple)
        self.assertEqual(len(DEFAULT_GRID_SIZE), 2)
        self.assertIsInstance(DEFAULT_GRID_SIZE[0], int)
        self.assertIsInstance(DEFAULT_GRID_SIZE[1], int)
        self.assertGreater(DEFAULT_GRID_SIZE[0], 0)
        self.assertGreater(DEFAULT_GRID_SIZE[1], 0)

    def test_markHorizontalLine_uses_constants(self):
        """Test that markHorizontalLine uses the correct constants."""
        img = markHorizontalLine(10, 10, 100, 10)
        self.assertEqual(img.size, IMAGE_DIMENSIONS)

        # Test with explicit default color
        img_default = markHorizontalLine(10, 10, 100, 10, color=DEFAULT_LINE_COLOR)
        self.assertEqual(img_default.size, IMAGE_DIMENSIONS)

    def test_overlayGrid_uses_constants(self):
        """Test that overlayGrid uses the correct constants."""
        # Test with explicit default parameters
        result_img = overlayGrid(
            self.test_image_path,
            grid_color=DEFAULT_GRID_COLOR,
            grid_size=DEFAULT_GRID_SIZE,
        )
        self.assertIsInstance(result_img, Image.Image)

    def test_image_processing_workflow(self):
        """Test a complete image processing workflow."""
        # Create an image with a line
        line_img = markHorizontalLine(0, 50, IMAGE_DIMENSIONS[0], 50, thickness=3)

        # Save the line image
        line_image_path = os.path.join(self.temp_dir, "line_image.png")
        line_img.save(line_image_path)

        # Apply grid overlay to the line image
        final_img = overlayGrid(line_image_path, grid_size=(8, 6))

        self.assertIsInstance(final_img, Image.Image)
        self.assertEqual(final_img.size, IMAGE_DIMENSIONS)

        # Clean up
        os.remove(line_image_path)

    def test_error_handling_io_error(self):
        """Test error handling for corrupted image files."""
        # Create a corrupted image file (not a valid image)
        corrupted_path = os.path.join(self.temp_dir, "corrupted.png")
        with open(corrupted_path, "w") as f:
            f.write("This is not an image file")

        with self.assertRaises(Exception):  # Should raise some kind of exception
            overlayGrid(corrupted_path)

        os.remove(corrupted_path)

    def test_overlayGrid_preserves_image_mode(self):
        """Test that overlayGrid preserves different image modes."""
        # Test with RGBA image
        rgba_path = os.path.join(self.temp_dir, "rgba_image.png")
        rgba_img = Image.new("RGBA", (100, 100), (255, 255, 255, 128))
        rgba_img.save(rgba_path)

        result_img = overlayGrid(rgba_path)
        self.assertEqual(result_img.mode, "RGBA")

        os.remove(rgba_path)

    # endregion


if __name__ == "__main__":
    unittest.main()
