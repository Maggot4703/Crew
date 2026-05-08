#!/usr/bin/python3
"""Tests for 0101 launch fallback behavior."""

import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

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

    @patch("gui.subprocess.run")
    def test_launch_remote_0101_server_syncs_project_before_starting(self, mock_run):
        app = CrewGUI.__new__(CrewGUI)
        app._find_local_0101_project_root = MagicMock(
            return_value=Path("/home/me/Notebooks/0101/0101")
        )
        mock_run.side_effect = [
            subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="/home/me/Desktop/0101/0101/src/public_html/server.py",
                stderr="",
            ),
            subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr=""),
            subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr=""),
            subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="started|/home/me/Desktop/0101/0101/src/public_html/server.py|192.168.1.50",
                stderr="",
            ),
        ]

        status, remote_url = app._launch_remote_0101_server()

        self.assertEqual(status, "started")
        self.assertEqual(remote_url, "http://192.168.1.50:8080/0101.html")
        rsync_call = next(
            call for call in mock_run.call_args_list if call.args[0][0] == "rsync"
        )
        self.assertIn(
            "me@p48:/home/me/Desktop/0101/0101/",
            rsync_call.args[0],
        )

    def test_build_0101_window_title_candidates_includes_url_fragments(self):
        candidates = CrewGUI._build_0101_window_title_candidates(
            "http://192.168.0.8:8080/0101.html"
        )

        self.assertIn("0101", candidates)
        self.assertIn("0101.html", candidates)
        self.assertIn("192.168.0.8:8080", candidates)
        self.assertIn("192.168.0.8", candidates)

    @patch("webbrowser.open")
    def test_open_0101_url_uses_browser_when_no_existing_0101_window(self, mock_open):
        app = CrewGUI.__new__(CrewGUI)
        app._resize_0101_window_async = MagicMock()
        app._activate_existing_0101_window = MagicMock(return_value=False)

        app._open_0101_url("http://192.168.0.8:8080/0101.html")

        mock_open.assert_called_once_with("http://192.168.0.8:8080/0101.html", new=0)
        app._resize_0101_window_async.assert_called_once_with(
            "http://192.168.0.8:8080/0101.html"
        )

    @patch("webbrowser.open")
    def test_open_0101_url_reuses_existing_0101_window_before_opening(self, mock_open):
        app = CrewGUI.__new__(CrewGUI)
        app._resize_0101_window_async = MagicMock()
        app._activate_existing_0101_window = MagicMock(return_value=True)

        app._open_0101_url("http://192.168.0.8:8080/0101.html")

        app._activate_existing_0101_window.assert_called_once_with(
            "http://192.168.0.8:8080/0101.html"
        )
        mock_open.assert_not_called()
        app._resize_0101_window_async.assert_called_once_with(
            "http://192.168.0.8:8080/0101.html"
        )

    @patch("gui.shutil.which")
    @patch("gui.subprocess.run")
    def test_activate_existing_0101_window_prefers_wmctrl_activation(
        self, mock_run, mock_which
    ):
        app = CrewGUI.__new__(CrewGUI)
        mock_which.side_effect = lambda tool: (
            f"/usr/bin/{tool}" if tool == "wmctrl" else None
        )
        mock_run.side_effect = [
            subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="0x01200007  0 host  0101.html - Chromium\n",
                stderr="",
            ),
            subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr=""),
        ]

        reused = app._activate_existing_0101_window("http://192.168.0.8:8080/0101.html")

        self.assertTrue(reused)
        self.assertEqual(
            mock_run.call_args_list[1].args[0], ["wmctrl", "-i", "-a", "0x01200007"]
        )

    @patch("gui.shutil.which")
    @patch("gui.subprocess.run")
    def test_resize_window_by_title_matches_wmctrl_listed_window(
        self, mock_run, mock_which
    ):
        app = CrewGUI.__new__(CrewGUI)
        mock_which.side_effect = lambda tool: (
            f"/usr/bin/{tool}" if tool == "wmctrl" else None
        )
        mock_run.side_effect = [
            subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="0x01200007  0 host  0101.html - Chromium\n",
                stderr="",
            ),
            subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr=""),
        ]

        resized = app._resize_window_by_title(
            ["0101.html", "0101"], 720, 1180, attempts=1
        )

        self.assertTrue(resized)
        self.assertEqual(mock_run.call_args_list[1].args[0][:3], ["wmctrl", "-i", "-r"])


if __name__ == "__main__":
    unittest.main()
