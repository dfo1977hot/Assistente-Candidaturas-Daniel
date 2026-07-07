"""Multi-agent session management use cases."""

from typing import Any

from acd.infrastructure.agents.registry import AgentRegistry
from acd.services.agents.supervisor_service import SupervisorService


def initialize_multi_agent_platform(
    supervisor_service: SupervisorService | None = None,
    registry: AgentRegistry | None = None,
) -> dict[str, Any]:
    """Initialize the multi-agent platform with all specialized agents.

    Args:
        supervisor_service: Supervisor service
        registry: Agent registry

    Returns:
        Initialization result
    """
    if registry is None:
        registry = AgentRegistry()

    if supervisor_service is None:
        supervisor_service = SupervisorService(registry=registry)

    # Create specialized agents
    agents = [
        ("Resume", "resume", "Manages resumes, versions, and optimizations"),
        ("ATS", "ats", "Analyzes job adherence and ATS score"),
        ("Automation", "automation", "Handles job application automation"),
        ("Career", "career", "Plans career development and skills"),
        ("Interview", "interview", "Prepares for interviews and simulations"),
        ("Analytics", "analytics", "Tracks KPIs and trends"),
        ("Workflow", "workflow", "Executes and monitors workflows"),
    ]

    created_agents = []
    for name, agent_type, description in agents:
        from acd.domain.agents.agent import Agent

        agent_entity = Agent(
            name=name,
            agent_type=agent_type,
            description=description,
            max_parallel_tasks=2,
            timeout_seconds=300,
            retry_count=3,
        )

        # Register in registry
        registry.register(agent_entity)
        created_agents.append(agent_entity.name)

    return {
        "success": True,
        "agents_initialized": created_agents,
        "supervisor_ready": True,
    }


def start_session(
    title: str,
    user_objective: str,
    supervisor_service: SupervisorService | None = None,
) -> dict[str, Any]:
    """Start a new multi-agent session.

    Args:
        title: Session title
        user_objective: User's objective
        supervisor_service: Supervisor service

    Returns:
        Session start result
    """
    if supervisor_service is None:
        supervisor_service = SupervisorService()

    session_id = supervisor_service.start_session(title, user_objective)

    return {
        "success": True,
        "session_id": session_id,
        "title": title,
        "objective": user_objective,
    }


def process_user_request(
    user_request: str,
    session_id: int | None = None,
    supervisor_service: SupervisorService | None = None,
) -> dict[str, Any]:
    """Process user request through multi-agent system.

    Args:
        user_request: User's request
        session_id: Optional session ID
        supervisor_service: Supervisor service

    Returns:
        Processing result
    """
    if supervisor_service is None:
        supervisor_service = SupervisorService()

    result = supervisor_service.process_user_request(user_request, session_id)

    return result


def get_session_status(
    session_id: int | None = None,
    supervisor_service: SupervisorService | None = None,
) -> dict[str, Any]:
    """Get status of current session.

    Args:
        session_id: Optional session ID
        supervisor_service: Supervisor service

    Returns:
        Session status
    """
    if supervisor_service is None:
        supervisor_service = SupervisorService()

    return supervisor_service.get_session_status(session_id)


def get_supervisor_status(supervisor_service: SupervisorService | None = None) -> dict[str, Any]:
    """Get supervisor and multi-agent platform status.

    Args:
        supervisor_service: Supervisor service

    Returns:
        Platform status
    """
    if supervisor_service is None:
        supervisor_service = SupervisorService()

    return supervisor_service.get_supervisor_status()


def end_session(
    session_id: int | None = None,
    supervisor_service: SupervisorService | None = None,
) -> dict[str, Any]:
    """End current session.

    Args:
        session_id: Optional session ID
        supervisor_service: Supervisor service

    Returns:
        End session result
    """
    if supervisor_service is None:
        supervisor_service = SupervisorService()

    return supervisor_service.end_session(session_id)
