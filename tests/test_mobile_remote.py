# flake8: noqa: E402
#!/usr/bin/env python3
"""Focused tests for the Crew LAN mobile remote."""

import json
import os
import sys
import tkinter as tk
import unittest
import urllib.parse
import urllib.request
from unittest.mock import patch

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from gui import CrewGUI  # noqa: E402
from mobile_remote import CrewMobileRemoteServer  # noqa: E402


class TestCrewMobileRemote(unittest.TestCase):
    """Verify mobile remote server and GUI integration."""

    def test_mobile_remote_server_status_and_action(self):
        actions = []

        def record_action(action, payload):
            actions.append((action, payload))
            return {"ok": True, "message": f"did {action}"}

        server = CrewMobileRemoteServer(
            host="127.0.0.1",
            port=0,
            token="test-token",
            status_callback=lambda: {"status": "Ready"},
            action_callback=record_action,
        )

        try:
            server.start()
            port = server.httpd.server_address[1]

            with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/api/status?token=test-token"
            ) as response:
                payload = json.loads(response.read().decode("utf-8"))
            self.assertEqual(payload["status"], "Ready")

            body = urllib.parse.urlencode(
                {
                    "token": "test-token",
                    "action": "send_crew_message",
                    "sender": "Mobile",
                    "recipient": "All",
                    "text": "Lights out",
                    "format": "json",
                }
            ).encode("utf-8")
            request = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/action",
                data=body,
                headers={"Accept": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request) as response:
                payload = json.loads(response.read().decode("utf-8"))
            self.assertTrue(payload["ok"])
            self.assertEqual(actions[0][0], "send_crew_message")
            self.assertEqual(actions[0][1]["text"], "Lights out")
        finally:
            server.stop()

    def test_gui_mobile_remote_actions_and_lifecycle(self):
        root = tk.Tk()
        root.withdraw()
        gui = CrewGUI(root)

        try:
            with patch.object(gui, "open_chatbot_dialog") as open_chatbot, patch(
                "tkinter.messagebox.showinfo"
            ):
                result = gui.handle_mobile_remote_action("open_chatbot")
                self.assertTrue(result["ok"])
                open_chatbot.assert_called_once()

                result = gui.handle_mobile_remote_action(
                    "send_crew_message",
                    {"sender": "Mobile", "recipient": "All", "text": "Bed check"},
                )
                self.assertTrue(result["ok"])
                messages = gui.message_router.get_messages(room="crew_multi_user")
                self.assertTrue(
                    any(
                        message["sender"] == "Mobile" and message["text"] == "Bed check"
                        for message in messages
                    )
                )

                gui.start_mobile_remote()
                self.assertIsNotNone(gui.mobile_remote_server)
                gui.stop_mobile_remote()
                self.assertIsNone(gui.mobile_remote_server)
        finally:
            if gui.mobile_remote_server is not None:
                gui.mobile_remote_server.stop()
            root.destroy()


if __name__ == "__main__":
    unittest.main()
