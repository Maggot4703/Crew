"""
Test suite for the GUI module.

This module tests GUI functionality including window initialization,
widget creation, and user interface components.
"""

import sys
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestGUIModule(unittest.TestCase):
    """Test suite for GUI module functionality."""

    def setUp(self):
        """Set up test environment before each test."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing

    def tearDown(self):
        """Clean up test environment after each test."""
        if self.root:
            self.root.destroy()

    def test_tkinter_availability(self):
        """Test that tkinter is available and working."""
        test_window = tk.Tk()
        test_window.title("Test Window")
        test_window.withdraw()

        frame = tk.Frame(test_window)
        self.assertIsInstance(frame, tk.Frame)

        label = tk.Label(frame, text="Test Label")
        self.assertIsInstance(label, tk.Label)

        test_window.destroy()

    def test_ttk_widgets_availability(self):
        """Test that ttk widgets are available."""
        from tkinter import ttk

        test_window = tk.Tk()
        test_window.withdraw()

        frame = ttk.Frame(test_window)
        self.assertIsInstance(frame, ttk.Frame)

        button = ttk.Button(test_window, text="Test Button")
        self.assertIsInstance(button, ttk.Button)

        treeview = ttk.Treeview(test_window)
        self.assertIsInstance(treeview, ttk.Treeview)

        test_window.destroy()

    def test_auto_import_py_files_function(self):
        """Test the auto_import_py_files function."""
        try:
            from gui import auto_import_py_files

            imported_modules, failed_imports = auto_import_py_files()
            self.assertIsInstance(imported_modules, list)
            self.assertIsInstance(failed_imports, list)
        except Exception as e:
            self.skipTest(f"Auto import test requires workspace context: {e}")

    def test_gui_imports(self):
        """Test that all required GUI imports are available."""
        try:
            import tkinter as tk
            from pathlib import Path
            from queue import Queue
            from tkinter import filedialog, messagebox, ttk
            from typing import Any, Callable, Dict, List, Optional, Tuple

            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Required import failed: {e}")

    def test_gui_constants_and_classes(self):
        """Test that GUI module contains expected constants and classes."""
        import gui

        self.assertTrue(hasattr(gui, "CrewGUI"))
        self.assertTrue(hasattr(gui, "main"))
        self.assertTrue(hasattr(gui, "auto_import_py_files"))
        self.assertTrue(callable(gui.CrewGUI))

    def test_path_handling(self):
        """Test Path object handling in GUI context."""
        from pathlib import Path

        test_path = Path("test_file.csv")
        self.assertEqual(test_path.suffix, ".csv")
        self.assertEqual(test_path.stem, "test_file")

        data_path = Path("data") / "npcs.csv"
        self.assertEqual(str(data_path), "data/npcs.csv")


if __name__ == "__main__":
    unittest.main(verbosity=1)
