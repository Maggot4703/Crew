#!/usr/bin/python3
"""
Test module for BMP to PNG conversion functionality.
"""

import sys
import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

import bmp2png
from Crew import get_version


class TestBMP2PNG(unittest.TestCase):
    """Test suite for BMP to PNG conversion."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.test_bmp_path = os.path.join(self.test_dir, "test.bmp")
        self.test_png_path = os.path.join(self.test_dir, "test.png")

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @patch("bmp2png.Image.open")
    @patch("os.makedirs")
    def test_convert_bmp_to_png_success(self, mock_makedirs, mock_image_open):
        """Test successful BMP to PNG conversion."""
        # Mock Image operations
        mock_image = MagicMock()
        mock_image_open.return_value = mock_image

        # Call the function
        result = bmp2png.convert_bmp_to_png(self.test_bmp_path, self.test_png_path)

        # Verify calls
        mock_image_open.assert_called_with(self.test_bmp_path)
        mock_image.save.assert_called_with(self.test_png_path, "PNG")
        mock_makedirs.assert_called_with(
            os.path.dirname(self.test_png_path), exist_ok=True
        )

        # Should return True for success
        self.assertTrue(result)

    @patch("bmp2png.Image.open")
    @patch("builtins.print")
    def test_convert_bmp_to_png_file_not_found(self, mock_print, mock_image_open):
        """Test conversion with non-existent BMP file."""
        mock_image_open.side_effect = FileNotFoundError("File not found")

        result = bmp2png.convert_bmp_to_png("nonexistent.bmp", "output.png")

        # Should return False
        self.assertFalse(result)

        # Should print error message
        mock_print.assert_called()
        error_calls = [
            call for call in mock_print.call_args_list if "not found" in str(call)
        ]
        self.assertGreater(len(error_calls), 0)

    @patch("bmp2png.Image.open")
    @patch("builtins.print")
    def test_convert_bmp_to_png_conversion_error(self, mock_print, mock_image_open):
        """Test conversion with IOError during processing."""
        mock_image_open.side_effect = IOError("Cannot process image")

        result = bmp2png.convert_bmp_to_png(self.test_bmp_path, self.test_png_path)

        # Should return False
        self.assertFalse(result)

        # Should print error message
        mock_print.assert_called()
        error_calls = [
            call
            for call in mock_print.call_args_list
            if "Error converting" in str(call)
        ]
        self.assertGreater(len(error_calls), 0)

    @patch("bmp2png.convert_bmp_to_png")
    @patch("glob.glob")
    @patch("os.path.isdir")
    @patch("os.makedirs")
    def test_batch_convert_bmps_in_directory(
        self, mock_makedirs, mock_isdir, mock_glob, mock_convert
    ):
        """Test batch conversion of BMP files."""
        # Mock directory setup
        mock_isdir.return_value = True
        mock_glob.return_value = [
            "input_dir/file1.bmp",
            "input_dir/file2.bmp",
            "input_dir/file3.bmp",
        ]
        mock_convert.return_value = True

        # Call batch conversion
        bmp2png.batch_convert_bmps_in_directory("input_dir", "output_dir")

        # Verify directory creation
        mock_makedirs.assert_called_with("output_dir", exist_ok=True)

        # Verify conversion calls (should convert all found BMP files)
        self.assertEqual(mock_convert.call_count, 3)

    @patch("os.path.isdir")
    @patch("builtins.print")
    def test_batch_convert_invalid_input_directory(self, mock_print, mock_isdir):
        """Test batch conversion with invalid input directory."""
        mock_isdir.return_value = False

        bmp2png.batch_convert_bmps_in_directory("invalid_dir", "output_dir")

        # Should print error message
        mock_print.assert_called()
        error_calls = [
            call for call in mock_print.call_args_list if "not found" in str(call)
        ]
        self.assertGreater(len(error_calls), 0)

    @patch("bmp2png.convert_bmp_to_png")
    @patch("glob.glob")
    @patch("os.path.isdir")
    @patch("os.makedirs")
    @patch("builtins.print")
    def test_batch_convert_no_bmp_files(
        self, mock_print, mock_makedirs, mock_isdir, mock_glob, mock_convert
    ):
        """Test batch conversion with no BMP files in directory."""
        mock_isdir.return_value = True
        mock_glob.return_value = []  # No BMP files found

        bmp2png.batch_convert_bmps_in_directory("input_dir", "output_dir")

        # Should not call convert function
        mock_convert.assert_not_called()

        # Should print message about no BMP files
        mock_print.assert_called()

    def test_main_function_execution(self):
        """Test that main function can be called without errors."""
        # This tests the placeholder main execution
        # Since it's mostly placeholder code, we just verify it doesn't crash
        try:
            # We can't easily test the actual main() since it has print statements
            # But we can verify the module structure is intact
            self.assertTrue(hasattr(bmp2png, "convert_bmp_to_png"))
            self.assertTrue(hasattr(bmp2png, "batch_convert_bmps_in_directory"))
            self.assertTrue(callable(bmp2png.convert_bmp_to_png))
            self.assertTrue(callable(bmp2png.batch_convert_bmps_in_directory))
        except Exception as e:
            self.fail(f"Main function structure test failed: {e}")

    def test_file_extension_handling(self):
        """Test that function handles different BMP file extensions."""
        test_cases = ["test.bmp", "test.BMP", "test.Bmp", "TEST.BMP"]

        for bmp_file in test_cases:
            with self.subTest(bmp_file=bmp_file):
                with patch("bmp2png.Image.open") as mock_open, patch("os.makedirs"):
                    mock_image = MagicMock()
                    mock_open.return_value = mock_image

                    bmp2png.convert_bmp_to_png(bmp_file, "output.png")

                    # Should attempt to open the file regardless of case
                    mock_open.assert_called_with(bmp_file)

    @patch("builtins.print")
    def test_error_message_formatting(self, mock_print):
        """Test that error messages are properly formatted."""
        # Test with non-existent file (simulate FileNotFoundError)
        with patch(
            "bmp2png.Image.open", side_effect=FileNotFoundError("File not found")
        ):
            bmp2png.convert_bmp_to_png("test.bmp", "output.png")

        # Verify error message was printed
        mock_print.assert_called()
        # Check that some informative message was printed
        printed_args = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any("test.bmp" in arg for arg in printed_args))


if __name__ == "__main__":
    unittest.main()
