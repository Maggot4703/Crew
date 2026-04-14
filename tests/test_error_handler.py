"""
Test suite for ErrorHandler module (error_handler.py).
Covers safe execution, error handling, and file validation utilities.
"""

import unittest
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from error_handler import safe_execute, handle_errors, safe_file_operation, validate_data, is_not_none, is_file_exists, is_csv_file, is_excel_file

class TestErrorHandler(unittest.TestCase):
    def test_is_not_none(self):
        self.assertTrue(is_not_none(123))
        self.assertFalse(is_not_none(None))

    def test_is_file_exists(self):
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as f:
            file_path = f.name
            f.write(b"data")
        self.assertTrue(is_file_exists(file_path))
        self.assertFalse(is_file_exists("nonexistent.txt"))
        import os
        os.remove(file_path)

    def test_is_csv_file(self):
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as f:
            f.write("a,b\n1,2")
            file_path = f.name
        self.assertTrue(is_csv_file(file_path))
        self.assertFalse(is_csv_file("file.txt"))
        import os
        os.remove(file_path)

    def test_is_excel_file(self):
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".xlsx", mode="wb", delete=False) as f:
            f.write(b"PK\x03\x04")
            file_path = f.name
        self.assertTrue(is_excel_file(file_path))
        self.assertFalse(is_excel_file("file.txt"))
        import os
        os.remove(file_path)

    # Add more tests for safe_execute, handle_errors, safe_file_operation, validate_data as needed

if __name__ == "__main__":
    unittest.main()
