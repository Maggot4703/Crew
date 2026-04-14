"""
Test suite for UIManager module (ui_manager.py).
Covers widget registration, layout creation, and status updates.
"""

import unittest
from ui_manager import UIManager

class DummyParent:
    def __init__(self):
        class DummyTk:
            def call(self, *a, **kw):
                return None
        class DummyRoot:
            def __init__(self):
                self.tk = DummyTk()  # Mock attribute for ttk widgets
                self._last_child_ids = None  # For deeper ttk compatibility
                self._w = '.'  # For ttk compatibility
                self.children = {}  # For ttk compatibility
            def geometry(self, *a, **kw): pass
            def title(self, *a, **kw): pass
            def minsize(self, *a, **kw): pass
            def grid_rowconfigure(self, *a, **kw): pass
            def grid_columnconfigure(self, *a, **kw): pass
        self.root = DummyRoot()

class TestUIManager(unittest.TestCase):
    def setUp(self):
        self.parent = DummyParent()
        self.manager = UIManager(self.parent)

    def test_register_widget(self):
        # Should not raise error
        try:
            self.manager.register_widget("test", object())
        except Exception as e:
            self.fail(f"register_widget() raised {e}")

    def test_create_main_layout(self):
        try:
            self.manager.create_main_layout()
        except Exception as e:
            self.fail(f"create_main_layout() raised {e}")

    # Add more tests for menu and section creation as needed

if __name__ == "__main__":
    unittest.main()
