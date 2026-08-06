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
| AgentGoal | — | Contextos distintos | Preservar |
| ExecutionPlan | AgentSession | Contextos distintos | Preservar |
| PlanTask | AgentTask | Tabelas distintas | Preservar |
| ToolCall | AgentTool | Contextos distintos | Preservar |
| Memória de planejamento | AgentMemory | Modelos distintos | Preservar |
| ReasoningStep | — | Contexto distinto | Preservar |

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

## Resultado da comparação

- Não há `__tablename__` duplicado.
- As tabelas de planejamento e de multi-agentes são distintas no manifesto ORM.
- Sem uma migração schema-neutral aprovada, nenhum namespace pode ser removido
  ou convertido em alias.

---

## Direção futura

`acd.domain.agents` é o namespace canônico para novas capacidades
multi-agentes. A retirada de `acd.domain.agent` depende de substitutos para seu
contexto de metas e planejamento e permanece fora da Sprint F.
