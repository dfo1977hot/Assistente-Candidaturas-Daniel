"""Message Bus for agent communication."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
import logging
from typing import Any

from acd.domain.agents.message import MessageType

logger = logging.getLogger(__name__)

Message = dict[str, Any]
MessageHandler = Callable[[Message], None]


class MessageBus:
    """Central message bus for agent communication."""

    def __init__(self) -> None:
        """Initialize message bus."""
        self._messages: list[Message] = []
        self._subscribers: dict[MessageType, list[MessageHandler]] = {}

    def subscribe(
        self,
        message_type: MessageType,
        handler: MessageHandler,
    ) -> None:
        """Subscribe to a message type."""

        self._subscribers.setdefault(message_type, []).append(handler)

    def unsubscribe(
        self,
        message_type: MessageType,
        handler: MessageHandler,
    ) -> None:
        """Unsubscribe from a message type."""

        handlers = self._subscribers.get(message_type)
        if not handlers:
            return

        if handler in handlers:
            handlers.remove(handler)

        if not handlers:
            self._subscribers.pop(message_type, None)

    def publish(
        self,
        message_type: MessageType,
        sender_id: int | None,
        receiver_id: int | None,
        subject: str,
        content: str,
        payload: dict[str, Any] | None = None,
        task_id: int | None = None,
        requires_response: bool = False,
        session_id: int | None = None,
    ) -> Message:
        """Publish a message to the bus."""

        message: Message = {
            "id": len(self._messages) + 1,
            "message_type": message_type,
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "subject": subject,
            "content": content,
            "payload": payload or {},
            "task_id": task_id,
            "requires_response": requires_response,
            "session_id": session_id,
            "created_at": datetime.now(UTC),
            "read": False,
        }

        self._messages.append(message)

        for handler in self._subscribers.get(message_type, []):
            try:
                handler(message)
            except Exception:
                logger.exception(
                    "Error in message handler for message_type=%s",
                    message_type,
                )

        return message

    def get_messages(
        self,
        receiver_id: int | None = None,
        message_type: MessageType | None = None,
        unread_only: bool = False,
    ) -> list[Message]:
        """Return filtered messages."""

        messages = self._messages

        if receiver_id is not None:
            messages = [
                message
                for message in messages
                if (
                    message["receiver_id"] == receiver_id
                    or message["receiver_id"] is None
                )
            ]

        if message_type is not None:
            messages = [
                message
                for message in messages
                if message["message_type"] == message_type
            ]

        if unread_only:
            messages = [
                message
                for message in messages
                if not message["read"]
            ]

        return messages

    def mark_as_read(self, message_id: int) -> bool:
        """Mark a message as read."""

        for message in self._messages:
            if message["id"] == message_id:
                message["read"] = True
                return True

        return False

    def respond_to(
        self,
        original_message_id: int,
        sender_id: int | None,
        content: str,
        payload: dict[str, Any] | None = None,
    ) -> Message:
        """Send a response to a message."""

        original = next(
            (
                message
                for message in self._messages
                if message["id"] == original_message_id
            ),
            None,
        )

        if original is None:
            raise ValueError(
                f"Original message {original_message_id} not found"
            )

        response_type = {
            MessageType.NEED_APPROVAL: MessageType.TASK_ASSIGNED,
            MessageType.REQUEST_INFORMATION: MessageType.STATUS_UPDATE,
        }.get(
            original["message_type"],
            MessageType.STATUS_UPDATE,
        )

        return self.publish(
            message_type=response_type,
            sender_id=sender_id,
            receiver_id=original["sender_id"],
            subject=f"RE: {original['subject']}",
            content=content,
            payload=payload,
            task_id=original.get("task_id"),
            session_id=original.get("session_id"),
        )

    def get_message_history(self, session_id: int) -> list[Message]:
        """Return all messages of a session."""

        return [
            message
            for message in self._messages
            if message.get("session_id") == session_id
        ]

    def clear_messages(self, before_days: int = 30) -> int:
        """Remove old messages."""

        cutoff = datetime.now(UTC) - timedelta(days=before_days)

        original_count = len(self._messages)
        self._messages = [
            message
            for message in self._messages
            if message["created_at"] > cutoff
        ]

        return original_count - len(self._messages)
