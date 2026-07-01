"""Agent registry for dynamic agent management."""

from typing import Any, Callable, Coroutine

from acd.domain.agents.agent import Agent, AgentStatus


class AgentRegistry:
    """Registry for managing agents dynamically."""

    def __init__(self) -> None:
        """Initialize agent registry."""
        self._agents: dict[int, dict[str, Any]] = {}
        self._agent_by_name: dict[str, int] = {}
        self._agent_by_type: dict[str, list[int]] = {}

    def register(self, agent: Agent, handler: Callable[[dict[str, Any]], dict[str, Any]] | None = None) -> None:
        """Register an agent.

        Args:
            agent: Agent entity
            handler: Optional handler function for agent execution
        """
        agent_dict = {
            "id": agent.id,
            "name": agent.name,
            "type": agent.agent_type,
            "description": agent.description,
            "status": agent.status,
            "max_parallel_tasks": agent.max_parallel_tasks,
            "timeout_seconds": agent.timeout_seconds,
            "config": agent.config or {},
            "handler": handler,
        }

        self._agents[agent.id] = agent_dict
        self._agent_by_name[agent.name] = agent.id

        if agent.agent_type not in self._agent_by_type:
            self._agent_by_type[agent.agent_type] = []
        self._agent_by_type[agent.agent_type].append(agent.id)

    def unregister(self, agent_id: int) -> None:
        """Unregister an agent.

        Args:
            agent_id: Agent ID
        """
        if agent_id not in self._agents:
            return

        agent_dict = self._agents[agent_id]
        del self._agents[agent_id]
        del self._agent_by_name[agent_dict["name"]]

        if agent_dict["type"] in self._agent_by_type:
            self._agent_by_type[agent_dict["type"]].remove(agent_id)

    def get_agent(self, agent_id: int) -> dict[str, Any] | None:
        """Get agent by ID.

        Args:
            agent_id: Agent ID

        Returns:
            Agent dictionary or None
        """
        return self._agents.get(agent_id)

    def get_agent_by_name(self, name: str) -> dict[str, Any] | None:
        """Get agent by name.

        Args:
            name: Agent name

        Returns:
            Agent dictionary or None
        """
        agent_id = self._agent_by_name.get(name)
        return self._agents.get(agent_id) if agent_id else None

    def get_agents_by_type(self, agent_type: str) -> list[dict[str, Any]]:
        """Get all agents of a specific type.

        Args:
            agent_type: Agent type

        Returns:
            List of agent dictionaries
        """
        agent_ids = self._agent_by_type.get(agent_type, [])
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]

    def list_all_agents(self) -> list[dict[str, Any]]:
        """List all registered agents.

        Returns:
            List of agent dictionaries
        """
        return list(self._agents.values())

    def update_agent_status(self, agent_id: int, status: AgentStatus) -> bool:
        """Update agent status.

        Args:
            agent_id: Agent ID
            status: New status

        Returns:
            True if updated, False otherwise
        """
        if agent_id in self._agents:
            self._agents[agent_id]["status"] = status
            return True
        return False

    def get_available_agents(self, agent_type: str | None = None) -> list[dict[str, Any]]:
        """Get available agents (not busy).

        Args:
            agent_type: Optional filter by type

        Returns:
            List of available agents
        """
        agents = self.get_agents_by_type(agent_type) if agent_type else self.list_all_agents()
        return [a for a in agents if a["status"] in (AgentStatus.IDLE, AgentStatus.OFFLINE)]

    def get_agent_handler(self, agent_id: int) -> Callable[[dict[str, Any]], dict[str, Any]] | None:
        """Get handler function for agent.

        Args:
            agent_id: Agent ID

        Returns:
            Handler function or None
        """
        agent_dict = self._agents.get(agent_id)
        return agent_dict.get("handler") if agent_dict else None
