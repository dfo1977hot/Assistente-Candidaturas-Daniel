from __future__ import annotations

from typing import Any

from acd.infrastructure.agent.ai_orchestrator import AIOrchestrator
from acd.infrastructure.agent.tool_registry import DefaultToolRegistry
from acd.infrastructure.repositories.agent.agent_repository import AgentRepository
from acd.services.ai_execution_service import AgentMemoryService


def ask_agent(
    user_question: str,
    *,
    repository: AgentRepository | None = None,
    memory_service: AgentMemoryService | None = None,
    orchestrator: AIOrchestrator | None = None,
) -> dict[str, Any]:
    """Ask the agent a question.

    Args:
        user_question: User's question or request
        repository: Agent repository
        memory_service: Memory service
        orchestrator: AI orchestrator

    Returns:
        Agent analysis and response
    """
    if repository is None:
        repository = AgentRepository()
    if memory_service is None:
        memory_service = AgentMemoryService(repository)
    if orchestrator is None:
        orchestrator = AIOrchestrator(tool_registry=DefaultToolRegistry())

    # Analyze request
    analysis = orchestrator.analyze_request(user_question)

    # Save to memory
    memory_service.save_conversation(user_question, analysis.get("intent", "unknown"))

    # Get context
    context = orchestrator.context_builder.build()

    return {
        "success": True,
        "intent": analysis.get("intent"),
        "confidence": analysis.get("confidence"),
        "next_action": analysis.get("next_action"),
        "context_available": bool(context),
        "analysis": analysis,
    }
