# ACD – Plano de Migração da Arquitetura de Agentes

**Projeto:** Assistente de Candidaturas do Daniel (ACD)

**Sprint:** 0.3D

**Status:** Superseded by Sprint F namespace governance

---

# Objetivo

Este plano histórico supunha que `acd.domain.agent` e
`acd.domain.agents` representavam a mesma arquitetura. A Sprint F comprovou
que são contextos ORM distintos, com tabelas e consumidores distintos.
ADR-028 e o manifesto de 92 tabelas proíbem sua consolidação por nome.

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

# Registro histórico corrigido

O conflito de tabela descrito por este documento não existe no Registry atual:
os 92 nomes são únicos e ambos os contextos são carregados explicitamente.

---

# Estratégia substituta

A migração futura deve ser schema-neutral, preservar a Registry e as
serializações, e seguir a política em `legacy_retirement_policy.md`. O
desacoplamento ORM/domínio continua sob ADR-028.

---

# Regras

Durante a Sprint 0.3D:

- Não utilizar extend_existing=True
- Não duplicar tabelas ORM
- Não criar novas funcionalidades na arquitetura legada
- Toda nova funcionalidade será implementada apenas em
  acd.domain.agents

---

# Critério de reavaliação futura

Uma retirada só poderá ser proposta após prova de substituto para cada tabela e
consumidor do contexto de metas e planejamento.