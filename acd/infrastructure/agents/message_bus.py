from __future__ import annotations

"""Message Bus for agent communication."""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from acd.domain.agents.message import MessageType


class MessageBus:
    """Central message bus for agent communication."""

    def __init__(self) -> None:
        """Initialize message bus."""
        self._messages: list[dict[str, Any]] = []
        self._subscribers: dict[MessageType, list[Callable]] = {}
        self._pending_responses: dict[int, list[dict[str, Any]]] = {}

    def subscribe(self, message_type: MessageType, handler: Callable) -> None:
        """Subscribe to message type.

        Args:
            message_type: Message type to subscribe to
            handler: Handler function to call when message is published
        """
        if message_type not in self._subscribers:
            self._subscribers[message_type] = []
        self._subscribers[message_type].append(handler)

    def unsubscribe(self, message_type: MessageType, handler: Callable) -> None:
        """Unsubscribe from message type.

        Args:
            message_type: Message type
            handler: Handler function to remove
        """
        if message_type in self._subscribers:
            self._subscribers[message_type].remove(handler)

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
    ) -> dict[str, Any]:
        """Publish a message to the bus.

        Args:
            message_type: Type of message
            sender_id: Sender agent ID
            receiver_id: Receiver agent ID (None for broadcast)
            subject: Message subject
            content: Message content
            payload: Optional payload
            task_id: Optional related task ID
            requires_response: Whether response is required
            session_id: Optional session ID

        Returns:
            Message dictionary
        """
        message = {
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

        # Call subscribers
        if message_type in self._subscribers:
            for handler in self._subscribers[message_type]:
                try:
                    handler(message)
                except Exception as e:
                    # Log error but don't break
                    print(f"Error in message handler: {e}")

        return message

    def get_messages(
        self,
        receiver_id: int | None = None,
        message_type: MessageType | None = None,
        unread_only: bool = False,
    ) -> list[dict[str, Any]]:
        """Get messages.

        Args:
            receiver_id: Optional filter by receiver
            message_type: Optional filter by type
            unread_only: Only return unread messages

        Returns:
            List of messages
        """
        messages = self._messages

        if receiver_id is not None:
            messages = [
                m for m in messages if m["receiver_id"] == receiver_id or m["receiver_id"] is None
            ]

        if message_type is not None:
            messages = [m for m in messages if m["message_type"] == message_type]

        if unread_only:
            messages = [m for m in messages if not m["read"]]

        return messages

    def mark_as_read(self, message_id: int) -> bool:
        """Mark message as read.

        Args:
            message_id: Message ID

        Returns:
            True if marked, False if not found
        """
        for msg in self._messages:
            if msg["id"] == message_id:
                msg["read"] = True
                return True
        return False

    def respond_to(
        self,
        original_message_id: int,
        sender_id: int | None,
        content: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send a response to a message.

        Args:
            original_message_id: ID of message being responded to
            sender_id: Sender agent ID
            content: Response content
            payload: Optional payload

        Returns:
            Response message
        """
        # Find original message
        original = None
        for msg in self._messages:
            if msg["id"] == original_message_id:
                original = msg
                break

        if not original:
            raise ValueError(f"Original message {original_message_id} not found")

        # Determine response type
        response_type = MessageType.STATUS_UPDATE
        if original["message_type"] == MessageType.NEED_APPROVAL:
            response_type = MessageType.TASK_ASSIGNED
        elif original["message_type"] == MessageType.REQUEST_INFORMATION:
            response_type = MessageType.STATUS_UPDATE

        # Create response message
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

    def get_message_history(self, session_id: int) -> list[dict[str, Any]]:
        """Get all messages from a session.

        Args:
            session_id: Session ID

        Returns:
            List of messages in session
        """
        return [m for m in self._messages if m.get("session_id") == session_id]

    def clear_messages(self, before_days: int = 30) -> int:
        """Clear old messages (for cleanup).

        Args:
            before_days: Remove messages older than N days

        Returns:
            Number of messages removed
        """
        cutoff = datetime.now(UTC)
        cutoff = cutoff.replace(day=cutoff.day - before_days)

        original_count = len(self._messages)
        self._messages = [m for m in self._messages if m["created_at"] > cutoff]

        return original_count - len(self._messages)
