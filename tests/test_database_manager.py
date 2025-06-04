"""
Test suite for the DatabaseManager module.

This module tests database operations, data loading, saving,
and SQLite database functionality.
"""

import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database_manager import DatabaseManager
from errors import DatabaseError


class TestDatabaseManager(unittest.TestCase):
    """Test suite for DatabaseManager class functionality."""

    def setUp(self):
        """Set up test environment before each test."""
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "test_crew.db")
        self.test_csv_path = os.path.join(self.test_dir, "test_data.csv")

        # Create test CSV data
        test_csv_content = """NAME,ROLE,SQUAD,PRIMUS,SECUNDUS
John Doe,Captain,Alpha,Leadership,Tactics
Jane Smith,Engineer,Beta,Repair,Electronics
Bob Wilson,Medic,Alpha,Medicine,Chemistry"""

        with open(self.test_csv_path, "w") as f:
            f.write(test_csv_content)

    def tearDown(self):
        """Clean up test environment after each test."""
        for file_path in [self.test_db_path, self.test_csv_path]:
            if os.path.exists(file_path):
                os.remove(file_path)
        if os.path.exists(self.test_dir):
            import shutil

            shutil.rmtree(self.test_dir)

    def test_database_manager_initialization(self):
        """Test DatabaseManager initialization."""
        db = DatabaseManager(self.test_db_path)
        self.assertIsInstance(db, DatabaseManager)
        self.assertEqual(db.db_name, self.test_db_path)

    def test_context_manager_functionality(self):
        """Test DatabaseManager context manager functionality."""
        with DatabaseManager(self.test_db_path) as db:
            self.assertIsNotNone(db.conn)
            self.assertIsInstance(db.conn, sqlite3.Connection)

    def test_load_csv_data(self):
        """Test loading data from CSV file."""
        with DatabaseManager(self.test_db_path) as db:
            headers, data, groups = db.load_data(self.test_csv_path)

            # Check headers
            expected_headers = ["NAME", "ROLE", "SQUAD", "PRIMUS", "SECUNDUS"]
            self.assertEqual(headers, expected_headers)

            # Check data length
            self.assertEqual(len(data), 3)

            # Check first row data
            first_row = data[0]
            self.assertEqual(first_row[0], "John Doe")
            self.assertEqual(first_row[1], "Captain")

    def test_save_data_to_csv(self):
        """Test saving data to CSV file."""
        headers = ["NAME", "ROLE", "SQUAD"]
        data = [
            ["Alice Brown", "Pilot", "Gamma"],
            ["Charlie Green", "Navigator", "Gamma"],
        ]

        output_path = os.path.join(self.test_dir, "output.csv")

        with DatabaseManager(self.test_db_path) as db:
            result = db.save_data(output_path, headers, data)
            self.assertTrue(result)

            # Verify file was created
            self.assertTrue(os.path.exists(output_path))

    def test_load_nonexistent_file(self):
        """Test loading from non-existent file raises appropriate error."""
        with DatabaseManager(self.test_db_path) as db:
            with self.assertRaises(FileNotFoundError):
                db.load_data("nonexistent_file.csv")

    def test_data_grouping_functionality(self):
        """Test data grouping by SQUAD column."""
        with DatabaseManager(self.test_db_path) as db:
            headers, data, groups = db.load_data(self.test_csv_path)

            # Check that groups were created
            self.assertIsInstance(groups, dict)

            # Should have Alpha and Beta groups based on test data
            if "Alpha" in groups:
                alpha_group = groups["Alpha"]
                self.assertEqual(len(alpha_group), 2)

    def test_database_logging_setup(self):
        """Test that database logging is configured correctly."""
        db = DatabaseManager(self.test_db_path)
        db.setup_logging()

        # Check that logger exists
        self.assertIsNotNone(db.logger)
        self.assertEqual(db.logger.name, "DatabaseManager")

    def test_schema_version_handling(self):
        """Test database schema versioning."""
        db = DatabaseManager(self.test_db_path)
        self.assertEqual(db.SCHEMA_VERSION, "1.0")


if __name__ == "__main__":
    unittest.main()
