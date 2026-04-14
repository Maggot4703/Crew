"""
Test suite for FileManager module (file_manager.py).
"""
import unittest
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from file_manager import FileManager
import tempfile
import os

class TestFileManager(unittest.TestCase):
    def setUp(self):
        self.fm = FileManager()
        self.test_dir = tempfile.mkdtemp()
        self.test_csv = os.path.join(self.test_dir, "test.csv")
        self.test_txt = os.path.join(self.test_dir, "test.txt")
        # Create a sample CSV file
        with open(self.test_csv, "w") as f:
            f.write("col1,col2\n1,2\n3,4\n")
        # Create a sample TXT file
        with open(self.test_txt, "w") as f:
            f.write("Hello, world!\n")

    def tearDown(self):
        for f in [self.test_csv, self.test_txt]:
            if os.path.exists(f):
                os.remove(f)
        os.rmdir(self.test_dir)

    def test_get_supported_file_types(self):
        types = self.fm.get_supported_file_types()
        self.assertIsInstance(types, list)
        self.assertTrue(any("csv" in t[1] for t in types))

    def test_load_data_file(self):
        data, headers = self.fm.load_data_file(self.test_csv)
        self.assertEqual(headers, ["col1", "col2"])
        self.assertEqual(data, [["1", "2"], ["3", "4"]])

    def test_load_text_file(self):
        content = self.fm.load_text_file(self.test_txt)
        self.assertEqual(content.strip(), "Hello, world!")

    def test_is_data_file(self):
        self.assertTrue(self.fm.is_data_file(self.test_csv))
        self.assertFalse(self.fm.is_data_file(self.test_txt))

    def test_is_text_file(self):
        self.assertTrue(self.fm.is_text_file(self.test_txt))
        self.assertFalse(self.fm.is_text_file(self.test_csv))

if __name__ == "__main__":
    unittest.main()
