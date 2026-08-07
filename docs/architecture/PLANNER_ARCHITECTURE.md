# Planner Architecture

Versão

0.1

---

## Objetivo

O Planner é responsável por analisar oportunidades de emprego e propor a melhor estratégia de candidatura.

Ele não executa ações.

Ele apenas planeja.

---

# Entradas

- vaga
- empresa
- currículo
- perfil profissional
- histórico de candidaturas
- objetivos de carreira
- preferências do usuário

---

# Saídas

- aderência
- prioridade
- currículo recomendado
- carta recomendada
- palavras-chave ausentes
- probabilidade ATS
- salário sugerido
- cronograma
- plano de follow-up

---

# Responsabilidades

Analisar

↓

Planejar

↓

Recomendar

Nunca executar.

A execução pertence ao módulo Execution.

---

# Componentes

Job Analyzer

ATS Analyzer

Resume Selector

Salary Advisor

Strategy Planner

Timeline Planner

Recommendation Engine