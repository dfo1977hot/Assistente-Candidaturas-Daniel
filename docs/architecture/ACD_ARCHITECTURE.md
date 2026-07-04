# Assistente de Candidaturas do Daniel (ACD)

# Arquitetura Oficial

Versão: 1.0

---

# Visão Geral

O ACD é dividido em quatro camadas independentes.

```
                Interface (Presentation)
                        │
                        ▼
                Application Layer
                        │
                        ▼
                Domain Services
                        │
                        ▼
              Infrastructure / Database
```

---

# Domínio Funcional

O domínio do sistema é organizado em quatro grandes módulos.

```
Planner
        │
        ▼
Execution
        │
        ▼
Learning
        │
        ▼
Analytics
```

---

# Planner

Responsável por decidir:

- objetivo
- estratégia
- sequência
- raciocínio

Componentes

- AgentGoal
- ExecutionPlan
- ReasoningStep
- ToolCall

Não executa tarefas.

---

# Execution

Responsável por executar.

Componentes

- Agents
- Sessions
- Tasks
- Messages
- Capabilities
- Tools

Não decide estratégia.

---

# Learning

Responsável por aprender.

Componentes

- Learning Records
- Insights
- Outcomes
- Patterns
- Hypotheses

---

# Analytics

Responsável por medir.

Componentes

- Dashboards
- KPIs
- ATS
- Recomendações
- Relatórios

---

# Fluxo Geral

```
Objetivo

↓

Plano

↓

Raciocínio

↓

Execução

↓

Aprendizado

↓

Métricas

↓

Melhoria
```

---

# Regra de Ouro

Planner nunca executa.

Execution nunca decide.

Learning nunca altera execução.

Analytics nunca altera dados.

Cada camada possui responsabilidade única.

---

# Objetivo da Sprint 0.4

Eliminar acoplamentos entre módulos.

Cada camada poderá evoluir independentemente.
