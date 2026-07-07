"""Base agent implementation."""

from abc import ABC, abstractmethod
from typing import Any

from acd.domain.agents.message import MessageType
from acd.infrastructure.agents.capability_service import CapabilityService
from acd.infrastructure.agents.context import AgentContext
from acd.infrastructure.agents.message_bus import MessageBus
from acd.infrastructure.repositories.agents.agent_repository import AgentRepository


class BaseAgent(ABC):
    """Base class for all specialized agents."""

    def __init__(
        self,
        agent_id: int,
        agent_name: str,
        agent_type: str,
        message_bus: MessageBus | None = None,
        capability_service: CapabilityService | None = None,
        repository: AgentRepository | None = None,
    ) -> None:
        """Initialize base agent.

        Args:
            agent_id: Agent ID
            agent_name: Agent name
            agent_type: Agent type
            message_bus: Message bus
            capability_service: Capability service
            repository: Agent repository
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.agent_type = agent_type

        self.message_bus = message_bus or MessageBus()
        self.capability_service = capability_service or CapabilityService()
        self.repository = repository or AgentRepository()

        self.context: AgentContext | None = None
        self._execution_count = 0

    def set_context(self, context: AgentContext) -> None:
        """Set agent context.

        Args:
            context: Agent context
        """
        self.context = context

    def can_perform_action(self, action: str) -> bool:
        """Check if agent can perform action.

        Args:
            action: Action name

        Returns:
            True if can perform
        """
        if not self.context:
            return False
        return self.context.has_permission(action)

    def can_use_tool(self, tool_name: str) -> bool:
        """Check if agent can use tool.

        Args:
            tool_name: Tool name

        Returns:
            True if authorized
        """
        if not self.context:
            return False
        return self.context.can_use_tool(tool_name)

    def record_message(self, sender: str, content: str) -> None:
        """Record message in context.

        Args:
            sender: Sender name
            content: Message content
        """
        if self.context:
            self.context.add_message(sender, content)

    def record_decision(self, decision: str, reasoning: str) -> None:
        """Record decision in context.

        Args:
            decision: Decision made
            reasoning: Reasoning behind it
        """
        if self.context:
            self.context.add_decision(decision, reasoning)

    def send_message(
        self,
        receiver_id: int | None,
        message_type: MessageType,
        subject: str,
        content: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send message via message bus.

        Args:
            receiver_id: Receiver agent ID
            message_type: Message type
            subject: Subject
            content: Content
            payload: Payload

        Returns:
            Message
        """
        return self.message_bus.publish(
            message_type=message_type,
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            subject=subject,
            content=content,
            payload=payload,
            session_id=self.context.session_id if self.context else None,
        )

    @abstractmethod
    def execute_task(self, task_input: dict[str, Any]) -> dict[str, Any]:
        """Execute a task. Must be implemented by subclass.

        Args:
            task_input: Task input

        Returns:
            Task result
        """
        pass

    def process_message(self, message: dict[str, Any]) -> None:
        """Process incoming message. Can be overridden by subclass.

        Args:
            message: Message from bus
        """
        # Default: record message
        self.record_message(
            sender=f"Agent {message.get('sender_id')}",
            content=message.get("content", ""),
        )

    def finalize(self) -> dict[str, Any]:
        """Finalize agent execution and return results.

        Returns:
            Final results
        """
        self._execution_count += 1

        result = {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "execution_count": self._execution_count,
        }

        if self.context:
            result["decisions_made"] = len(self.context.decision_history)
            result["messages_processed"] = len(self.context.message_history)

        return result
