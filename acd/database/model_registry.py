"""
Registro centralizado dos modelos ORM do ACD.

Este módulo deve ser importado antes de qualquer chamada a:

    Base.metadata.create_all(...)

Sua única responsabilidade é garantir que todos os modelos
SQLAlchemy sejam registrados no Base.metadata exatamente uma vez.
"""

#
# ------------------------------------------------------------------
# IA LEGADO
# ------------------------------------------------------------------
#

from acd.domain.agent.agent_goal import AgentGoal
from acd.domain.agents.memory import AgentMemory
from acd.domain.agent.execution_plan import ExecutionPlan
from acd.domain.agent.reasoning_step import ReasoningStep
from acd.domain.agent.plan_task import PlanTask
from acd.domain.agent.tool_call import ToolCall

#
# ------------------------------------------------------------------
# MULTI-AGENT
#
# IMPORTANTE:
#
# enquanto ainda existir o domínio legado utilizando as
# mesmas tabelas (agent_tasks e agent_memory).
#
# ------------------------------------------------------------------
#

from acd.domain.agents.agent import Agent
from acd.domain.agents.capability import AgentCapability
from acd.domain.agents.message import AgentMessage
from acd.domain.agents.session import AgentSession
from acd.domain.agents.tool import AgentTool

#
# ------------------------------------------------------------------
# DOMÍNIOS FUTUROS
# ------------------------------------------------------------------
#

# from acd.domain.entities.application import Application
# from acd.domain.entities.company import Company

#
# Evita que o Ruff considere os imports como não utilizados.
#

__all__ = [
    "AgentGoal",
    "AgentMemory",
    "ExecutionPlan",
    "ReasoningStep",
    "PlanTask",
    "ToolCall",
    "Agent",
    "AgentCapability",
    "AgentMessage",
    "AgentSession",
    "AgentTool",
]