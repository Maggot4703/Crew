# flake8: noqa: E402
#!/usr/bin/env python3
"""Focused tests for Crew chat routing and persistence."""

import sys
import tempfile
import unittest
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from database_manager import DatabaseManager  # noqa: E402
from message_router import CrewMessageRouter  # noqa: E402


class TestCrewMessageRouter(unittest.TestCase):
    """Verify chat metadata, persistence, and room scoping."""

    def test_send_message_persists_and_reloads(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "chat.db"
            db_manager = DatabaseManager(str(db_path))
            router = CrewMessageRouter(db_manager)

            message = router.send_message(
                "Captain",
                ["Navigator", "Doctor"],
                "Set course for Regina.",
                room="bridge",
                file_meta={"filename": "orders.txt", "filepath": "/tmp/orders.txt"},
            )

            self.assertTrue(message["id"])
            self.assertEqual(message["room"], "bridge")
            self.assertEqual(message["recipients"], ["Navigator", "Doctor"])

            reloaded_router = CrewMessageRouter(DatabaseManager(str(db_path)))
            messages = reloaded_router.get_messages(room="bridge")
            self.assertEqual(len(messages), 1)
            self.assertEqual(messages[0]["sender"], "Captain")
            self.assertEqual(messages[0]["file"]["filename"], "orders.txt")

    def test_undo_and_clear_are_room_scoped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "chat.db"
            router = CrewMessageRouter(DatabaseManager(str(db_path)))

            router.send_message("Captain", ["All"], "Bridge update", room="bridge")
            router.send_message("Captain", ["All"], "Engineering update", room="engine")
            router.send_message(
                "Captain", ["All"], "Second bridge update", room="bridge"
            )

            self.assertTrue(router.undo_last_user_message("Captain", room="bridge"))
            self.assertEqual(len(router.get_messages(room="bridge")), 1)
            self.assertEqual(len(router.get_messages(room="engine")), 1)

            router.clear_messages(room="bridge")
            self.assertEqual(router.get_messages(room="bridge"), [])
            self.assertEqual(len(router.get_messages(room="engine")), 1)


if __name__ == "__main__":
    unittest.main()
