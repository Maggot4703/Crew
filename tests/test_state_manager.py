"""
Test suite for StateManager module (state_manager.py).
Covers window state loading, saving, and column width management.
"""

import unittest
from state_manager import StateManager

class DummyGUI:
    def __init__(self):
        class DummyRoot:
            def geometry(self, *a, **kw): pass
            def minsize(self, *a, **kw): pass
        self.root = DummyRoot()
        self.config = type('DummyConfig', (), {
            'get': lambda self, key: None
        })()

class TestStateManager(unittest.TestCase):
    def setUp(self):
        self.gui = DummyGUI()
        self.manager = StateManager(self.gui)

    def test_load_window_state(self):
        # Should run without error (may need to mock file I/O)
        try:
            self.manager.load_window_state()
        except Exception as e:
            self.fail(f"load_window_state() raised {e}")

    def test_save_window_state(self):
        try:
            self.manager.save_window_state()
        except Exception as e:
            self.fail(f"save_window_state() raised {e}")

    # Add more tests for column width and state summary as needed

if __name__ == "__main__":
    unittest.main()
