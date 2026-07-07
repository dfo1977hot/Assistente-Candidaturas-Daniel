"""Capability-Based Access Control (CBAC) service."""

from datetime import UTC, datetime
from typing import Any


class CapabilityService:
    """Service for managing agent capabilities and permissions."""

    def __init__(self) -> None:
        """Initialize capability service."""
        self._capabilities: dict[int, list[str]] = {}  # agent_id -> capability names
        self._tools: dict[int, dict[str, Any]] = {}  # agent_id -> tool configuration
        self._tool_usage: dict[int, dict[str, int]] = {}  # agent_id -> tool usage count

    def grant_capability(self, agent_id: int, capability: str) -> None:
        """Grant a capability to an agent."""
        if agent_id not in self._capabilities:
            self._capabilities[agent_id] = []

        if capability not in self._capabilities[agent_id]:
            self._capabilities[agent_id].append(capability)

    def revoke_capability(self, agent_id: int, capability: str) -> bool:
        """Revoke a capability from an agent."""
        if (
            agent_id in self._capabilities
            and capability in self._capabilities[agent_id]
        ):
            self._capabilities[agent_id].remove(capability)
            return True

        return False

    def has_capability(self, agent_id: int, capability: str) -> bool:
        """Check whether the agent has a capability."""
        return capability in self._capabilities.get(agent_id, [])

    def get_capabilities(self, agent_id: int) -> list[str]:
        """Return all capabilities for an agent."""
        return self._capabilities.get(agent_id, [])

    def authorize_tool(
        self,
        agent_id: int,
        tool_name: str,
        max_calls_per_session: int | None = None,
        max_calls_per_day: int | None = None,
        requires_approval: bool = False,
    ) -> None:
        """Authorize a tool for an agent."""
        if agent_id not in self._tools:
            self._tools[agent_id] = {}

        self._tools[agent_id][tool_name] = {
            "tool_name": tool_name,
            "max_calls_per_session": max_calls_per_session,
            "max_calls_per_day": max_calls_per_day,
            "requires_approval": requires_approval,
            "authorized_at": datetime.now(UTC),
        }

        self.grant_capability(agent_id, f"use_tool_{tool_name}")

    def revoke_tool(self, agent_id: int, tool_name: str) -> bool:
        """Revoke authorization for a tool."""
        if (
            agent_id in self._tools
            and tool_name in self._tools[agent_id]
        ):
            del self._tools[agent_id][tool_name]
            self.revoke_capability(agent_id, f"use_tool_{tool_name}")
            return True

        return False

    def can_use_tool(self, agent_id: int, tool_name: str) -> bool:
        """Return whether the agent can use the tool."""
        return f"use_tool_{tool_name}" in self._capabilities.get(agent_id, [])

    def get_authorized_tools(self, agent_id: int) -> dict[str, Any]:
        """Return all authorized tools for an agent."""
        return self._tools.get(agent_id, {})

    def record_tool_usage(self, agent_id: int, tool_name: str) -> bool:
        """Record tool usage."""
        if agent_id not in self._tool_usage:
            self._tool_usage[agent_id] = {}

        if tool_name not in self._tool_usage[agent_id]:
            self._tool_usage[agent_id][tool_name] = 0

        tool_config = self._tools.get(agent_id, {}).get(tool_name)
        if tool_config is None:
            return False

        usage_count = self._tool_usage[agent_id][tool_name]

        max_calls = tool_config.get("max_calls_per_session")
        if max_calls is not None and usage_count >= max_calls:
            return False

        self._tool_usage[agent_id][tool_name] += 1
        return True

    def get_tool_usage(self, agent_id: int, tool_name: str) -> int:
        """Return the number of times a tool has been used."""
        return self._tool_usage.get(agent_id, {}).get(tool_name, 0)

    def reset_tool_usage(self, agent_id: int | None = None) -> None:
        """Reset tool usage counters."""
        if agent_id is None:
            self._tool_usage.clear()
            return

        self._tool_usage[agent_id] = {}

    def requires_approval(self, agent_id: int, tool_name: str) -> bool:
        """Return whether the tool requires approval."""
        tool_config = self._tools.get(agent_id, {}).get(tool_name)
        return (
            tool_config.get("requires_approval", False)
            if tool_config is not None
            else False
        )