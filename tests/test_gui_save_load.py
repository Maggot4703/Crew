import os
import tempfile
import unittest
import tkinter as tk
from unittest.mock import patch
from pathlib import Path

# Ensure gui.py is importable
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
import gui

class TestCrewGUISaveLoad(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = gui.CrewGUI(self.root)
        self.temp_dir = tempfile.mkdtemp()
        self.test_data = [["A", "B", "C"], [1, 2, 3], [4, 5, 6]]
        self.headers = ["Col1", "Col2", "Col3"]
        self.app.headers = self.headers
        self.app.current_data = self.test_data[1:]

    def tearDown(self):
        self.root.destroy()
        for f in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, f))
        os.rmdir(self.temp_dir)

    def test_save_and_load_csv(self):
        file_path = os.path.join(self.temp_dir, "test.csv")
        self.app._save_to_file(file_path, self.test_data[1:])
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        self.assertIn(",".join(self.headers) + "\n", lines[0])
        self.assertIn(",".join(map(str, self.test_data[1])) + "\n", lines[1])

    def test_save_and_load_txt(self):
        file_path = os.path.join(self.temp_dir, "test.txt")
        self.app._save_to_file(file_path, self.test_data[1:])
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(",".join(self.headers), content)
        self.assertIn(",".join(map(str, self.test_data[2])), content)

    @patch("tkinter.messagebox.showerror")
    def test_save_to_file_error(self, mock_showerror):
        # Simulate error by passing invalid path
        bad_path = "/nonexistent_dir/test.csv"
        self.app._save_to_file(bad_path, self.test_data[1:])
        # Process the event loop to allow root.after callbacks to run
        self.root.update()  # This will process pending events
        mock_showerror.assert_called()

if __name__ == "__main__":
    unittest.main()
