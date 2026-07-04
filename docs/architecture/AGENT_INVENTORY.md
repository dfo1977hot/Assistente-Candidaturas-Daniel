# Inventário da Arquitetura de Agentes

## Objetivo

Mapear todas as entidades, repositórios, serviços e testes
relacionados à arquitetura de agentes.

---

# Domínio

| Arquitetura Legada | Arquitetura Atual | Situação | Decisão |
|--------------------|-------------------|----------|----------|
| AgentGoal | — | Não migrado | Avaliar |
| ExecutionPlan | AgentSession | Parcial | Revisar |
| Task | AgentTask | Duplicado | Migrar |
| ToolCall | AgentTool | Parcial | Revisar |
| AgentMemory | AgentMemory | Duplicado | Migrar |
| ReasoningStep | — | Não migrado | Avaliar |

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

# Conflitos Identificados

- Duplicidade de ORM para `agent_tasks`
- Duplicidade de ORM para `agent_memory`
- Dois repositórios paralelos
- Dois modelos de domínio coexistindo

---

# Próximas ações

- Migrar testes da arquitetura legada
- Consolidar repositórios
- Remover imports antigos
- Eliminar o pacote `acd.domain.agent`