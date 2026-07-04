# Comparação das Arquiteturas de Agentes

Projeto: Assistente de Candidaturas do Daniel (ACD)

Sprint: 0.3D

---

# Objetivo

Comparar a arquitetura legada (`acd.domain.agent`)
com a arquitetura atual (`acd.domain.agents`).

---

## Domínio

| Legado | Atual | Equivalência | Situação |
|---------|-------|--------------|----------|
| AgentGoal | — | Não existe | Implementar |
| ExecutionPlan | AgentSession | Parcial | Revisar |
| Task | AgentTask | Alta | Migrar |
| ToolCall | AgentTool | Parcial | Revisar |
| AgentMemory | AgentMemory | Alta | Migrar |
| ReasoningStep | — | Não existe | Implementar |

---

## Repositórios

| Legado | Atual | Situação |
|---------|-------|----------|
| repositories/agent | repositories/agents | Ambos existem |

---

## Serviços

| Serviço | Status |
|----------|--------|
| services/agents | Em produção |
| services/agent | Não existe |

---

## Testes

| Arquivo | Arquitetura |
|----------|-------------|
| test_ai_orchestrator.py | Legada |
| test_multi_agent.py | Atual |

---

## Conflitos

- agent_tasks
- agent_memory

---

## Objetivo Final

Ao final da Sprint 0.3D deverá existir apenas:

acd/domain/agents

acd/infrastructure/repositories/agents

acd/services/agents
