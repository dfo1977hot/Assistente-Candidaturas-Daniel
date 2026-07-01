"""Capability-Based Access Control (CBAC) service."""

from typing import Any
from datetime import datetime


class CapabilityService:
    """Service for managing agent capabilities and permissions."""

    def __init__(self) -> None:
        """Initialize capability service."""
        self._capabilities: dict[int, list[str]] = {}  # agent_id -> list of capability names
        self._tools: dict[int, dict[str, Any]] = {}  # agent_id -> tool_name -> tool config
        self._tool_usage: dict[int, dict[str, int]] = {}  # agent_id -> tool_name -> usage count

    def grant_capability(self, agent_id: int, capability: str) -> None:
        """Grant a capability to an agent.

        Args:
            agent_id: Agent ID
            capability: Capability name
        """
        if agent_id not in self._capabilities:
            self._capabilities[agent_id] = []

        if capability not in self._capabilities[agent_id]:
            self._capabilities[agent_id].append(capability)

    def revoke_capability(self, agent_id: int, capability: str) -> bool:
        """Revoke a capability from an agent.

        Args:
            agent_id: Agent ID
            capability: Capability name

        Returns:
            True if revoked, False otherwise
        """
        if agent_id in self._capabilities:
            if capability in self._capabilities[agent_id]:
                self._capabilities[agent_id].remove(capability)
                return True
        return False

    def has_capability(self, agent_id: int, capability: str) -> bool:
        """Check if agent has capability.

        Args:
            agent_id: Agent ID
            capability: Capability name

        Returns:
            True if agent has capability
        """
        return capability in self._capabilities.get(agent_id, [])

    def get_capabilities(self, agent_id: int) -> list[str]:
        """Get all capabilities for agent.

        Args:
            agent_id: Agent ID

        Returns:
            List of capabilities
        """
        return self._capabilities.get(agent_id, [])

    def authorize_tool(
        self,
        agent_id: int,
        tool_name: str,
        max_calls_per_session: int | None = None,
        max_calls_per_day: int | None = None,
        requires_approval: bool = False,
    ) -> None:
        """Authorize a tool for an agent.

        Args:
            agent_id: Agent ID
            tool_name: Tool name
            max_calls_per_session: Max calls per session
            max_calls_per_day: Max calls per day
            requires_approval: Whether tool requires approval
        """
        if agent_id not in self._tools:
            self._tools[agent_id] = {}

        self._tools[agent_id][tool_name] = {
            "tool_name": tool_name,
            "max_calls_per_session": max_calls_per_session,
            "max_calls_per_day": max_calls_per_day,
            "requires_approval": requires_approval,
            "authorized_at": datetime.utcnow(),
        }

        # Grant corresponding capability
        self.grant_capability(agent_id, f"use_tool_{tool_name}")

    def revoke_tool(self, agent_id: int, tool_name: str) -> bool:
        """Revoke tool access from agent.

        Args:
            agent_id: Agent ID
            tool_name: Tool name

        Returns:
            True if revoked, False otherwise
        """
        if agent_id in self._tools and tool_name in self._tools[agent_id]:
            del self._tools[agent_id][tool_name]
            self.revoke_capability(agent_id, f"use_tool_{tool_name}")
            return True
        return False

    def can_use_tool(self, agent_id: int, tool_name: str) -> bool:
        """Check if agent can use tool.

        Args:
            agent_id: Agent ID
            tool_name: Tool name

        Returns:
            True if agent is authorized
        """
        return f"use_tool_{tool_name}" in self._capabilities.get(agent_id, [])

    def get_authorized_tools(self, agent_id: int) -> dict[str, Any]:
        """Get all authorized tools for agent.

        Args:
            agent_id: Agent ID

        Returns:
            Dictionary of tool configurations
        """
        return self._tools.get(agent_id, {})

    def record_tool_usage(self, agent_id: int, tool_name: str) -> bool:
        """Record tool usage by agent.

        Args:
            agent_id: Agent ID
            tool_name: Tool name

        Returns:
            True if within limits, False if exceeds limit
        """
        if agent_id not in self._tool_usage:
            self._tool_usage[agent_id] = {}

        if tool_name not in self._tool_usage[agent_id]:
            self._tool_usage[agent_id][tool_name] = 0

        # Get tool config
        tool_config = self._tools.get(agent_id, {}).get(tool_name)
        if not tool_config:
            return False

        # Check limits
        usage_count = self._tool_usage[agent_id][tool_name]
        if tool_config.get("max_calls_per_session") and usage_count >= tool_config["max_calls_per_session"]:
            return False

        # Record usage
        self._tool_usage[agent_id][tool_name] += 1
        return True

    def get_tool_usage(self, agent_id: int, tool_name: str) -> int:
        """Get usage count for tool.

        Args:
            agent_id: Agent ID
            tool_name: Tool name

        Returns:
            Usage count
        """
        return self._tool_usage.get(agent_id, {}).get(tool_name, 0)

    def reset_tool_usage(self, agent_id: int | None = None) -> None:
        """Reset tool usage counters.

        Args:
            agent_id: Optional agent ID (if None, reset all)
        """
        if agent_id:
            if agent_id in self._tool_usage:
                self._tool_usage[agent_id] = {}
        else:
            self._tool_usage = {}

    def requires_approval(self, agent_id: int, tool_name: str) -> bool:
        """Check if tool requires approval.

        Args:
            agent_id: Agent ID
            tool_name: Tool name

        Returns:
            True if requires approval
        """
        tool_config = self._tools.get(agent_id, {}).get(tool_name)
        return tool_config.get("requires_approval", False) if tool_config else False
