"""Tests for data handling utilities in Crew.py"""

import csv
import os
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Crew import read_csv_builtin, read_csv_pandas, read_file


class TestDataHandling(unittest.TestCase):
    """Test suite for data handling functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv_path = os.path.join(self.temp_dir, "test.csv")
        with open(self.test_csv_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Name", "Role", "Company"])
            writer.writerow(["Alice", "Captain", "StarCorp"])

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_csv_path):
            os.remove(self.test_csv_path)
        os.rmdir(self.temp_dir)

    def test_read_csv_builtin(self):
        """Test read_csv_builtin function."""
        data = read_csv_builtin(self.test_csv_path)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)  # Header + 1 data row

    def test_read_csv_pandas(self):
        """Test read_csv_pandas function."""
        df = read_csv_pandas(self.test_csv_path)
        self.assertIsInstance(df, pd.DataFrame)

    def test_read_file_nonexistent(self):
        """Test read_file with non-existent file."""
        result = read_file("nonexistent_file.csv")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
