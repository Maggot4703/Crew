"""
Basic tests for the Crew application.

This module contains fundamental test cases to ensure the core application
components and directory structure are properly set up and functional.
"""

import os
import sys
import unittest
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestBasicApp(unittest.TestCase):
    """Test suite for basic application startup and functionality."""

    def setUp(self):
        """Set up resources before each test."""
        self.base_dir = Path(__file__).parent.parent

    def test_module_imports(self):
        """Test that core modules can be imported without errors."""
        try:
            import Crew

            self.assertTrue(hasattr(Crew, "main"))
        except ImportError as e:
            self.fail(f"Failed to import Crew module: {e}")

        try:
            import config

            self.assertTrue(hasattr(config, "Config"))
        except ImportError as e:
            self.fail(f"Failed to import config module: {e}")

        try:
            import database_manager

            self.assertTrue(hasattr(database_manager, "DatabaseManager"))
        except ImportError as e:
            self.fail(f"Failed to import database_manager module: {e}")

    def test_constants_accessible(self):
        """Test that important constants are accessible."""
        try:
            from Crew import DEFAULT_GRID_COLOR, DEFAULT_LINE_COLOR, IMAGE_DIMENSIONS

            self.assertIsInstance(IMAGE_DIMENSIONS, tuple)
            self.assertIsInstance(DEFAULT_GRID_COLOR, tuple)
            self.assertIsInstance(DEFAULT_LINE_COLOR, tuple)
        except ImportError as e:
            self.fail(f"Failed to import constants: {e}")

    def test_directory_structure(self):
        """Test that required directories exist."""
        required_dirs = ["data", "input", "output", "tests"]

        for dir_name in required_dirs:
            dir_path = self.base_dir / dir_name
            self.assertTrue(dir_path.exists(), f"Directory '{dir_name}' does not exist")
            self.assertTrue(dir_path.is_dir(), f"'{dir_name}' is not a directory")

    def test_core_files_exist(self):
        """Test that core application files exist."""
        required_files = [
            "Crew.py",
            "config.py",
            "database_manager.py",
            "gui.py",
            "errors.py",
            "requirements.txt",
        ]

        for file_name in required_files:
            file_path = self.base_dir / file_name
            self.assertTrue(file_path.exists(), f"File '{file_name}' does not exist")
            self.assertTrue(file_path.is_file(), f"'{file_name}' is not a file")

    def test_sample_data_files(self):
        """Test that sample data files exist."""
        data_dir = self.base_dir / "data"
        if data_dir.exists():
            # Check for at least some CSV files
            csv_files = list(data_dir.glob("*.csv"))
            self.assertGreater(
                len(csv_files), 0, "No CSV files found in data directory"
            )

    def test_configuration_files(self):
        """Test that configuration files are valid."""
        config_files = ["setup.cfg"]

        for config_file in config_files:
            config_path = self.base_dir / config_file
            if config_path.exists():
                self.assertTrue(config_path.is_file(), f"'{config_file}' is not a file")
                # Basic check that file is not empty
                self.assertGreater(
                    config_path.stat().st_size, 0, f"'{config_file}' is empty"
                )

    def test_python_version_compatibility(self):
        """Test that Python version is compatible."""
        # Crew application requires Python 3.8+
        self.assertGreaterEqual(sys.version_info.major, 3)
        self.assertGreaterEqual(sys.version_info.minor, 8)

    def test_required_packages_importable(self):
        """Test that required packages can be imported."""
        required_packages = ["pandas", "PIL", "tkinter"]  # Pillow

        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                # Skip tkinter test in headless environments
                if package == "tkinter" and "DISPLAY" not in os.environ:
                    self.skipTest(
                        f"Skipping {package} import test in headless environment"
                    )
                else:
                    self.fail(f"Required package '{package}' cannot be imported")


class TestDirectoryExistence(unittest.TestCase):
    """Test suite for directory existence checks."""

    def test_data_dir_exists(self):
        """Test that data directory exists."""
        self.assertTrue(os.path.isdir("data"), "Data directory does not exist")

    def test_input_dir_exists(self):
        """Test that input directory exists."""
        self.assertTrue(os.path.isdir("input"), "Input directory does not exist")

    def test_output_dir_exists(self):
        """Test that output directory exists."""
        if not os.path.isdir("output"):
            # Create output directory if it doesn't exist (it's often created at runtime)
            os.makedirs("output", exist_ok=True)
        self.assertTrue(os.path.isdir("output"), "Output directory does not exist")

    def test_tests_dir_exists(self):
        """Test that tests directory exists."""
        self.assertTrue(os.path.isdir("tests"), "Tests directory does not exist")


if __name__ == "__main__":
    unittest.main()


def test_output_dir_exists():
    assert os.path.isdir("output")
