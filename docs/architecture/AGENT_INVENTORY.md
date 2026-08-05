# Inventário da Arquitetura de Agentes

## Objetivo

Mapear todas as entidades, repositórios, serviços e testes
relacionados à arquitetura de agentes.

---

# Domínio

| Arquitetura Legada | Arquitetura Atual | Situação | Decisão |
|--------------------|-------------------|----------|----------|
| AgentGoal | — | Contexto distinto | Preservar |
| ExecutionPlan | AgentSession | Contexto distinto | Preservar |
| PlanTask | AgentTask | Tabelas distintas | Preservar |
| ToolCall | AgentTool | Contexto distinto | Preservar |
| Agent memory de planejamento | AgentMemory | Modelos e tabelas distintos | Preservar |
| ReasoningStep | — | Contexto distinto | Preservar |

---

# Repositórios

| Legado | Atual | Situação |
|---------|-------|----------|
| infrastructure/repositories/agent | infrastructure/repositories/agents | Ambos existem |

---

# Serviços

| Serviço | Arquitetura |
|----------|-------------|
| services/agents | Atual |
| services/agent | Não existe |

---

# Testes

| Arquivo | Arquitetura |
|----------|-------------|
| tests/test_ai_orchestrator.py | Legada |
| tests/test_multi_agent.py | Atual |

---

# Decisão da Sprint F

- Não há tabelas ORM duplicadas entre os contextos.
- `agent` possui cinco tabelas de metas e planejamento; `agents` possui sete
  tabelas de multi-agentes.
- Os repositórios atendem contratos e contextos distintos.
- `acd.domain.agents` é o namespace canônico para comportamento novo de
  multi-agentes; `acd.domain.agent` permanece canônico para planejamento.

---

# Próximas ações

- Preservar as duas áreas enquanto seus contratos e tabelas existirem.
- Executar qualquer renomeação futura como migração schema-neutral com aliases
  explícitos, testes de identidade e validação do Registry.