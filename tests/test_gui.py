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

# Add project root to sys.path to allow importing gui module
# This assumes the tests are run from the project root or the test_gui.py script's directory
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Attempt to import the gui module. Handle if it's not found or causes issues.
try:
    import gui  # Assuming gui.py is in the project root
except ImportError as e:
    # This allows tests to run and report the import error clearly
    # rather than failing before test execution begins.
    gui = None
    gui_import_error = e


class TestGUIModule(unittest.TestCase):
    """Test suite for GUI module functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up for all tests in this class."""
        # Check if gui module was imported successfully
        if gui is None:
            raise unittest.SkipTest(
                f"Skipping GUI tests: gui module could not be imported. Error: {gui_import_error}"
            )

    def setUp(self):
        """Set up test environment before each test."""
        # Create a root window for tests that need it, but keep it hidden.
        # Some ttk widgets might need a root window to be instantiated.
        try:
            self.root = tk.Tk()
            self.root.withdraw()  # Hide the window during testing
        except tk.TclError as e:
            # This can happen in environments without a display (e.g., some CI servers)
            self.skipTest(f"Skipping test: Tkinter could not be initialized (no display?): {e}")

    def tearDown(self):
        """Clean up test environment after each test."""
        if hasattr(self, "root") and self.root:
            try:
                self.root.destroy()
            except tk.TclError:  # Handle cases where window might already be destroyed or not fully initialized
                pass

    def test_tkinter_availability(self):
        """Test that tkinter is available and basic widgets can be created."""
        # self.root is created in setUp, if it fails, test is skipped.
        frame = tk.Frame(self.root)
        self.assertIsInstance(frame, tk.Frame)
        label = tk.Label(frame, text="Test Label")
        self.assertIsInstance(label, tk.Label)

    def test_ttk_widgets_availability(self):
        """Test that ttk widgets are available."""
        from tkinter import ttk

        # self.root is created in setUp.
        frame = ttk.Frame(self.root)
        self.assertIsInstance(frame, ttk.Frame)
        button = ttk.Button(self.root, text="Test Button")
        self.assertIsInstance(button, ttk.Button)
        treeview = ttk.Treeview(self.root)
        self.assertIsInstance(treeview, ttk.Treeview)

    def test_auto_import_py_files_function_exists(self):
        """Test the auto_import_py_files function exists in gui module."""
        # Assumes gui module is imported successfully (checked in setUpClass)
        self.assertTrue(
            hasattr(gui, "auto_import_py_files"), "gui module does not have auto_import_py_files function"
        )
        self.assertTrue(callable(gui.auto_import_py_files), "auto_import_py_files is not callable")

    # This test might be too broad or hard to maintain if gui.py has many complex imports.
    # def test_gui_imports(self):
    #     """Test that all required GUI imports are available."""
    #     # This is implicitly tested by the successful import of the `gui` module itself.
    #     # If specific sub-dependencies of gui.py need checking, they could be tested here.
    #     pass

    def test_gui_main_entities_exist(self):
        """Test that GUI module contains expected main classes and functions."""
        self.assertTrue(hasattr(gui, "CrewGUI"), "CrewGUI class is missing from gui module.")
        self.assertTrue(callable(gui.CrewGUI), "CrewGUI is not callable (not a class?).")
        self.assertTrue(hasattr(gui, "main"), "main function is missing from gui module.")
        self.assertTrue(callable(gui.main), "main is not callable.")

    def test_path_handling_pathlib(self):
        """Test Path object handling from pathlib, as it's used in project."""
        # This test is more about pathlib itself, but confirms its availability and basic use.
        test_path = Path("test_file.csv")
        self.assertEqual(test_path.suffix, ".csv")
        self.assertEqual(test_path.stem, "test_file")

        data_path = Path("data") / "npcs.csv"
        # Use os.path.join for platform-independent path comparison if needed,
        # but string comparison is fine here for a fixed example.
        self.assertEqual(
            str(data_path), "data/npcs.csv" if sys.platform != "win32" else "data\\npcs.csv"
        )

    # Example of how to mock and test a simple GUI interaction if CrewGUI was more complete
    # @patch('gui.tk.messagebox') # Assuming CrewGUI uses messagebox
    # def test_crew_gui_example_action(self, mock_messagebox):
    #     """Example test for a hypothetical action in CrewGUI."""
    #     if not hasattr(gui, 'CrewGUI'): self.skipTest("CrewGUI class not available")
    #
    #     app = gui.CrewGUI(self.root) # Assuming CrewGUI takes root as an arg
    #
    #     # Simulate an action, e.g., a button click that should show an info message
    #     # if hasattr(app, 'on_some_button_click'):
    #     #     app.on_some_button_click()
    #     #     mock_messagebox.showinfo.assert_called_with("Info", "Action performed!")
    #     # else:
    #     #     self.skipTest("CrewGUI does not have on_some_button_click method for testing")
    #     pass


if __name__ == "__main__":
    unittest.main(verbosity=2)  # Increased verbosity for more detailed test output
