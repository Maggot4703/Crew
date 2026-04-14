"""
Test suite for event_manager.py (Event Manager module).
"""
import unittest
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import event_manager

class TestEventManager(unittest.TestCase):
    def test_dummy(self):
        # Replace with real tests for event_manager.py functions/classes
        self.assertTrue(True)

if __name__ == "__main__":
    unittest.main()
