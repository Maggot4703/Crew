#!/usr/bin/env python3
"""Tests for layout.py compatibility helpers."""

import unittest

import layout


class DummyRoot:
    def __init__(self):
        self.title_value = None

    def title(self, value):
        self.title_value = value


def test_layout():
    """Run a minimal smoke test for the layout helper."""
    config = layout.initialize_gui()
    assert isinstance(config, dict)
    assert "configured" in config


class TestLayoutHelpers(unittest.TestCase):
    """Test suite for lightweight layout compatibility behavior."""

    def test_initialize_gui_without_root(self):
        config = layout.initialize_gui()
        self.assertEqual(config["title"], "Crew Manager")
        self.assertFalse(config["configured"])

    def test_initialize_gui_with_root(self):
        root = DummyRoot()
        config = layout.initialize_gui(root, title="Crew Test")
        self.assertTrue(config["configured"])
        self.assertEqual(config["title"], "Crew Test")
        self.assertEqual(root.title_value, "Crew Test")


if __name__ == "__main__":
    unittest.main()
