"""
Crew Message Router and Logger
=============================

Handles routing messages between crew members and logging all communications.
"""

import logging
import threading
from typing import List, Dict, Any, Optional
from datetime import datetime

class CrewMessageRouter:
    def __init__(self):
        self.lock = threading.Lock()
        self.messages: List[Dict[str, Any]] = []  # Each message: {sender, recipients, text, timestamp, file}
        self.logger = logging.getLogger("CrewMessageRouter")

    def undo_last_user_message(self, user: str) -> bool:
        """Remove the last message sent by the specified user. Returns True if a message was removed."""
        with self.lock:
            for i in range(len(self.messages) - 1, -1, -1):
                if self.messages[i]["sender"] == user:
                    del self.messages[i]
                    self.logger.info(f"Last message from {user} undone.")
                    return True
        return False

    def send_message(self, sender: str, recipients: List[str], text: str, file_meta: Optional[dict] = None) -> None:
        msg = {
            "sender": sender,
            "recipients": recipients,
            "text": text,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if file_meta:
            msg["file"] = file_meta
        with self.lock:
            self.messages.append(msg)
        self.logger.info(f"Message from {sender} to {recipients}: {text} {'[file attached]' if file_meta else ''}")

    def get_messages(self, recipient: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.lock:
            if recipient is None:
                return list(self.messages)
            return [m for m in self.messages if recipient in m["recipients"] or m["sender"] == recipient]

    def clear_messages(self) -> None:
        with self.lock:
            self.messages.clear()
        self.logger.info("All messages cleared.")
