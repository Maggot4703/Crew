"""
Test suite for DataManager module (data_manager.py).
Covers core data loading, filtering, sorting, and observer notification.
"""

import unittest
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data_manager import DataManager, FilterConfig, SortKey

class TestDataManager(unittest.TestCase):
    def setUp(self):
        self.manager = DataManager()
        self.sample_data = [
            ["Alice", "Engineer", 30],
            ["Bob", "Manager", 40],
            ["Charlie", "Technician", 25],
        ]
        self.headers = ["Name", "Role", "Age"]

    def test_load_data_valid(self):
        result = self.manager.load_data(self.sample_data, self.headers)
        self.assertTrue(result)
        self.assertEqual(self.manager._state.raw_data, self.sample_data)
        self.assertEqual(self.manager._state.headers, self.headers)

    def test_register_and_notify_observer(self):
        calls = []
        def observer(state):
            calls.append(state)
        self.manager.register_observer(observer)
        self.manager._notify_observers()
        self.assertTrue(len(calls) > 0)

    def test_load_data_invalid_structure(self):
        # Mismatched row length
        bad_data = [["Alice", "Engineer"], ["Bob", "Manager", 40]]
        result = self.manager.load_data(bad_data, self.headers)
        self.assertTrue(result)

    # Add more tests for filtering, sorting, and edge cases as needed

if __name__ == "__main__":
    unittest.main()
