"""Agent context manager."""

from typing import Any
from datetime import datetime


class AgentContext:
    """Context for an agent."""

    def __init__(
        self,
        agent_id: int,
        agent_name: str,
        objective: str,
        session_id: int | None = None,
    ) -> None:
        """Initialize agent context.

        Args:
            agent_id: Agent ID
            agent_name: Agent name
            objective: Current objective
            session_id: Optional session ID
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.objective = objective
        self.session_id = session_id

        # Profile and user data
        self.user_profile: dict[str, Any] = {}
        self.career_goals: list[dict[str, Any]] = []
        self.applications: list[dict[str, Any]] = []

        # Agent-specific
        self.authorized_tools: list[str] = []
        self.authorized_capabilities: list[str] = []
        self.permissions: dict[str, bool] = {}

        # Memory
        self.temporary_memory: dict[str, Any] = {}
        self.persistent_memory: dict[str, Any] = {}

        # History
        self.message_history: list[dict[str, Any]] = []
        self.decision_history: list[dict[str, Any]] = []
        self.execution_history: list[dict[str, Any]] = []

        # Constraints
        self.constraints: dict[str, Any] = {}
        self.restrictions: dict[str, Any] = {}

        # Timestamps
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def add_user_profile(self, profile: dict[str, Any]) -> "AgentContext":
        """Add user profile data.

        Args:
            profile: User profile dict

        Returns:
            Self for chaining
        """
        self.user_profile.update(profile)
        self.updated_at = datetime.utcnow()
        return self

    def add_career_goals(self, goals: list[dict[str, Any]]) -> "AgentContext":
        """Add career goals.

        Args:
            goals: List of career goals

        Returns:
            Self for chaining
        """
        self.career_goals = goals
        self.updated_at = datetime.utcnow()
        return self

    def add_tools(self, tools: list[str]) -> "AgentContext":
        """Authorize tools for agent.

        Args:
            tools: List of tool names

        Returns:
            Self for chaining
        """
        self.authorized_tools = tools
        self.updated_at = datetime.utcnow()
        return self

    def add_permissions(self, permissions: dict[str, bool]) -> "AgentContext":
        """Add permissions.

        Args:
            permissions: Permission dict

        Returns:
            Self for chaining
        """
        self.permissions.update(permissions)
        self.updated_at = datetime.utcnow()
        return self

    def set_constraints(self, constraints: dict[str, Any]) -> "AgentContext":
        """Set operational constraints.

        Args:
            constraints: Constraint dict

        Returns:
            Self for chaining
        """
        self.constraints = constraints
        self.updated_at = datetime.utcnow()
        return self

    def store_temporary(self, key: str, value: Any) -> None:
        """Store data in temporary memory.

        Args:
            key: Memory key
            value: Memory value
        """
        self.temporary_memory[key] = value
        self.updated_at = datetime.utcnow()

    def store_persistent(self, key: str, value: Any) -> None:
        """Store data in persistent memory.

        Args:
            key: Memory key
            value: Memory value
        """
        self.persistent_memory[key] = value
        self.updated_at = datetime.utcnow()

    def get_temporary(self, key: str, default: Any = None) -> Any:
        """Get data from temporary memory.

        Args:
            key: Memory key
            default: Default value if not found

        Returns:
            Memory value or default
        """
        return self.temporary_memory.get(key, default)

    def get_persistent(self, key: str, default: Any = None) -> Any:
        """Get data from persistent memory.

        Args:
            key: Memory key
            default: Default value if not found

        Returns:
            Memory value or default
        """
        return self.persistent_memory.get(key, default)

    def add_message(self, sender: str, content: str) -> None:
        """Add to message history.

        Args:
            sender: Sender name
            content: Message content
        """
        self.message_history.append({
            "sender": sender,
            "content": content,
            "timestamp": datetime.utcnow(),
        })

    def add_decision(self, decision: str, reasoning: str) -> None:
        """Add to decision history.

        Args:
            decision: Decision made
            reasoning: Reasoning behind decision
        """
        self.decision_history.append({
            "decision": decision,
            "reasoning": reasoning,
            "timestamp": datetime.utcnow(),
        })

    def has_permission(self, permission: str) -> bool:
        """Check if agent has permission.

        Args:
            permission: Permission name

        Returns:
            True if permitted
        """
        return self.permissions.get(permission, False)

    def can_use_tool(self, tool_name: str) -> bool:
        """Check if agent can use tool.

        Args:
            tool_name: Tool name

        Returns:
            True if authorized
        """
        return tool_name in self.authorized_tools

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary.

        Returns:
            Context dictionary
        """
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "objective": self.objective,
            "session_id": self.session_id,
            "user_profile": self.user_profile,
            "career_goals": self.career_goals,
            "applications": self.applications,
            "authorized_tools": self.authorized_tools,
            "permissions": self.permissions,
            "constraints": self.constraints,
            "message_count": len(self.message_history),
            "decision_count": len(self.decision_history),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ContextManager:
    """Manager for agent contexts."""

    def __init__(self) -> None:
        """Initialize context manager."""
        self._contexts: dict[int, AgentContext] = {}
        self._session_contexts: dict[int, list[int]] = {}

    def create_context(
        self,
        agent_id: int,
        agent_name: str,
        objective: str,
        session_id: int | None = None,
    ) -> AgentContext:
        """Create a new agent context.

        Args:
            agent_id: Agent ID
            agent_name: Agent name
            objective: Current objective
            session_id: Optional session ID

        Returns:
            New context
        """
        context = AgentContext(agent_id, agent_name, objective, session_id)
        self._contexts[agent_id] = context

        if session_id:
            if session_id not in self._session_contexts:
                self._session_contexts[session_id] = []
            self._session_contexts[session_id].append(agent_id)

        return context

    def get_context(self, agent_id: int) -> AgentContext | None:
        """Get agent context.

        Args:
            agent_id: Agent ID

        Returns:
            Agent context or None
        """
        return self._contexts.get(agent_id)

    def get_session_contexts(self, session_id: int) -> list[AgentContext]:
        """Get all contexts for a session.

        Args:
            session_id: Session ID

        Returns:
            List of contexts
        """
        agent_ids = self._session_contexts.get(session_id, [])
        return [self._contexts[aid] for aid in agent_ids if aid in self._contexts]

    def clear_context(self, agent_id: int) -> None:
        """Clear agent context.

        Args:
            agent_id: Agent ID
        """
        if agent_id in self._contexts:
            del self._contexts[agent_id]

    def clear_session_contexts(self, session_id: int) -> None:
        """Clear all contexts for a session.

        Args:
            session_id: Session ID
        """
        agent_ids = self._session_contexts.get(session_id, [])
        for aid in agent_ids:
            self.clear_context(aid)
        del self._session_contexts[session_id]
