#!/usr/bin/python3
"""Tests for main window startup geometry behavior."""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import Config
from gui import CrewGUI


class TestWindowGeometryStartup(unittest.TestCase):
    """Verify default startup sizing and centering math."""

    def test_build_centered_geometry_uses_800_square_window(self):
        """Main window geometry should be 800x800 and centered."""
        geometry = CrewGUI.build_centered_geometry(1920, 1080)
        self.assertEqual(geometry, "800x800+560+140")

    def test_build_centered_geometry_clamps_offsets_to_zero(self):
        """Centering should not generate negative offsets on small screens."""
        geometry = CrewGUI.build_centered_geometry(640, 700)
        self.assertEqual(geometry, "800x800+0+0")

    def test_build_0101_window_size_matches_graphical_layout(self):
        """0101 browser window should fit the 600px layout plus browser chrome."""
        size = CrewGUI.build_0101_window_size()
        self.assertEqual(size, (720, 1180))

    def test_config_defaults_match_startup_window_size(self):
        """Configuration defaults should align with startup geometry."""
        self.assertEqual(Config.DEFAULT_CONFIG["window_size"], "800x800")
        self.assertEqual(Config.DEFAULT_CONFIG["min_window_size"], "800x800")

    def test_load_window_state_uses_saved_geometry_if_valid(self):
        """Saved valid geometry should be restored, not overridden."""
        app = CrewGUI.__new__(CrewGUI)
        app.root = MagicMock()
        app.root.winfo_screenwidth.return_value = 1920
        app.root.winfo_screenheight.return_value = 1080
        app.column_visibility = {}
        app.config = MagicMock()
        app.config.get.side_effect = lambda key, default=None: {
            "window_size": "1020x1080",
            "min_window_size": "800x600",
            "column_widths": {},
            "column_visibility": {},
        }.get(key, default)

        app.load_window_state()

        app.root.geometry.assert_called_with("1020x1080")
        app.root.minsize.assert_called_with(800, 600)


if __name__ == "__main__":
    unittest.main()
