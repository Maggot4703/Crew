"""Crew chat routing, metadata, and persistence helpers."""

import logging
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class ChatMessage:
    """Structured chat message used by Crew chat surfaces."""

    id: str
    room: str
    sender: str
    recipients: List[str]
    text: str
    timestamp: str
    file: Optional[Dict[str, Any]] = None
    reply_to_id: Optional[str] = None
    status: str = "sent"
    edited_at: Optional[str] = None


class CrewMessageRouter:
    """Route and persist Crew chat messages."""

    def __init__(self, db_manager: Optional[Any] = None):
        self.lock = threading.Lock()
        self.logger = logging.getLogger("CrewMessageRouter")
        self.db_manager = db_manager
        self.messages: List[Dict[str, Any]] = []
        if self.db_manager is not None:
            self.messages = self.db_manager.load_chat_messages()

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _normalize_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        normalized = ChatMessage(
            id=str(message.get("id") or uuid4()),
            room=str(message.get("room") or "crew_multi_user"),
            sender=str(message.get("sender") or "Unknown"),
            recipients=list(dict.fromkeys(message.get("recipients") or ["All"])),
            text=str(message.get("text") or ""),
            timestamp=str(message.get("timestamp") or self._timestamp()),
            file=message.get("file"),
            reply_to_id=message.get("reply_to_id"),
            status=str(message.get("status") or "sent"),
            edited_at=message.get("edited_at"),
        )
        return asdict(normalized)

    def undo_last_user_message(self, user: str, room: Optional[str] = None) -> bool:
        """Remove the last message sent by the specified user."""
        removed_message = None
        with self.lock:
            for i in range(len(self.messages) - 1, -1, -1):
                message = self.messages[i]
                if message["sender"] == user and (
                    room is None or message["room"] == room
                ):
                    removed_message = self.messages.pop(i)
                    break
            if removed_message is None:
                return False
            if self.db_manager is not None:
                self.db_manager.clear_chat_messages(room=removed_message["room"])
                for message in self.messages:
                    if message["room"] == removed_message["room"]:
                        self.db_manager.save_chat_message(message)
        self.logger.info("Last message from %s undone in room %s.", user, room or "*")
        return True

    def send_message(
        self,
        sender: str,
        recipients: List[str],
        text: str,
        file_meta: Optional[dict] = None,
        room: str = "crew_multi_user",
        reply_to_id: Optional[str] = None,
        status: str = "sent",
    ) -> Dict[str, Any]:
        """Store and optionally persist a chat message."""
        message = self._normalize_message(
            {
                "sender": sender,
                "recipients": recipients,
                "text": text,
                "room": room,
                "file": file_meta,
                "reply_to_id": reply_to_id,
                "status": status,
            }
        )
        with self.lock:
            self.messages.append(message)
            if self.db_manager is not None:
                self.db_manager.save_chat_message(message)
        self.logger.info(
            "Message %s from %s to %s in room %s%s",
            message["id"],
            sender,
            recipients,
            room,
            " [file attached]" if file_meta else "",
        )
        return dict(message)

    def get_messages(
        self, recipient: Optional[str] = None, room: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Return filtered message history."""
        with self.lock:
            messages = list(self.messages)
        if room is not None:
            messages = [message for message in messages if message["room"] == room]
        if recipient is None:
            return messages
        return [
            message
            for message in messages
            if recipient in message["recipients"] or message["sender"] == recipient
        ]

    def clear_messages(self, room: Optional[str] = None) -> None:
        """Clear in-memory and persisted messages."""
        with self.lock:
            if room is None:
                self.messages.clear()
            else:
                self.messages = [
                    message for message in self.messages if message["room"] != room
                ]
            if self.db_manager is not None:
                self.db_manager.clear_chat_messages(room=room)
        self.logger.info("Cleared chat messages for room %s.", room or "*")
