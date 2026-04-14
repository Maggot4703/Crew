"""
Test suite for ScriptManager module (script_manager.py).
Covers script file discovery, validation, and execution.
"""

import unittest
from script_manager import ScriptManager

class TestScriptManager(unittest.TestCase):
    def setUp(self):
        # Provide a dummy UI callback
        self.manager = ScriptManager(scripts_dir="/tmp", ui_callback=lambda msg, err: None)

    def test_get_script_files(self):
        result = self.manager.get_script_files()
        self.assertIsInstance(result, list)

    def test_validate_script_dir(self):
        # Use the correct method name as implemented
        if hasattr(self.manager, 'validate_script_dir'):
            valid, msg = self.manager.validate_script_dir()
        else:
            valid, msg = self.manager.validate_script_directory()
        self.assertIsInstance(valid, bool)
        self.assertIsInstance(msg, str)

    # Add more tests for script execution and error handling as needed

if __name__ == "__main__":
    unittest.main()
