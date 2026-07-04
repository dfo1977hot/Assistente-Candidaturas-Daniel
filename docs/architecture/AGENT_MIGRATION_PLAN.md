# ACD – Plano de Migração da Arquitetura de Agentes

**Projeto:** Assistente de Candidaturas do Daniel (ACD)

**Sprint:** 0.3D

**Status:** Em andamento

---

# Objetivo

Eliminar gradualmente a arquitetura legada (`acd.domain.agent`)
e consolidar toda a plataforma sobre a nova arquitetura
(`acd.domain.agents`).

O objetivo é manter apenas um conjunto de entidades ORM,
repositórios, serviços e testes relacionados aos Agentes.

---

# Arquitetura Atual

Atualmente coexistem duas arquiteturas:

## Arquitetura Legada

```
acd/domain/agent/
acd/infrastructure/repositories/agent/
```

Principais entidades:

- AgentGoal
- ExecutionPlan
- Task
- ToolCall
- AgentMemory
- ReasoningStep

---

## Nova Arquitetura

```
acd/domain/agents/
acd/infrastructure/repositories/agents/
acd/services/agents/
```

Principais entidades:

- Agent
- AgentTask
- AgentSession
- AgentMessage
- AgentCapability
- AgentTool
- AgentMemory

---

# Problema Atual

Durante a execução do pytest ocorre o erro:

```
sqlalchemy.exc.InvalidRequestError

Table 'agent_tasks' is already defined
```

A causa é a coexistência de dois modelos ORM que registram
a mesma tabela no mesmo Base.metadata.

Exemplo:

```
acd.domain.agent.task

↓

__tablename__ = "agent_tasks"

acd.domain.agents.task

↓

__tablename__ = "agent_tasks"
```

O mesmo ocorre com:

```
agent_memory
```

---

# Estratégia de Migração

A migração ocorrerá em cinco etapas.

## Etapa 1

Inventário completo.

Status:

☑ Concluído

---

## Etapa 2

Comparação funcional entre os dois modelos.

Status:

⬜ Em andamento

---

## Etapa 3

Migração dos testes.

Status:

⬜ Pendente

---

## Etapa 4

Migração dos repositórios.

Status:

⬜ Pendente

---

## Etapa 5

Remoção definitiva da arquitetura legada.

Status:

⬜ Pendente

---

# Regras

Durante a Sprint 0.3D:

- Não utilizar extend_existing=True
- Não duplicar tabelas ORM
- Não criar novas funcionalidades na arquitetura legada
- Toda nova funcionalidade será implementada apenas em
  acd.domain.agents

---

# Critério de Conclusão

A Sprint será considerada concluída quando:

- existir apenas uma implementação ORM para cada tabela;
- todos os testes passarem;
- todos os serviços utilizarem acd.domain.agents;
- acd.domain.agent puder ser removido do projeto.