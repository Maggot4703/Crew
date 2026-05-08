#!/usr/bin/python3
"""Tests for 0101 launch fallback behavior."""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from gui import CrewGUI  # noqa: E402


class Test0101LaunchFallback(unittest.TestCase):
    """Verify 0101 launch falls back to the local server when SSH fails."""

    def test_launch_0101_server_falls_back_to_local_when_remote_fails(self):
        app = CrewGUI.__new__(CrewGUI)
        app.update_status = MagicMock()
        app._open_0101_url = MagicMock()
        app._show_0101_launch_error = MagicMock()
        app._launch_remote_0101_server = MagicMock(
            side_effect=RuntimeError("ssh target unavailable")
        )
        app._launch_local_0101_server = MagicMock(
            return_value=("started", "http://localhost:8080/0101.html")
        )

        app._launch_0101_server()

        app._launch_local_0101_server.assert_called_once_with()
        app._open_0101_url.assert_called_once_with("http://localhost:8080/0101.html")
        app._show_0101_launch_error.assert_not_called()
        app.update_status.assert_called_once()
        status_message = app.update_status.call_args.args[0]
        self.assertIn("using local server", status_message)
        self.assertIn("http://localhost:8080/0101.html", status_message)


if __name__ == "__main__":
    unittest.main()
