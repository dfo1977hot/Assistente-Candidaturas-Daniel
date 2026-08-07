# ACD Development Constitution

Version: 1.0

---

# Article I — Domain First

Toda regra de negócio pertence ao domínio.

A interface nunca implementa regras de negócio.

---

# Article II — Service Layer

Toda operação passa pelos Services.

Nenhuma Page conversa diretamente com Repository.

---

# Article III — Repository Pattern

Repositories apenas persistem dados.

Nunca implementam regras de negócio.

---

# Article IV — Documentation First

Toda alteração estrutural deve ser documentada antes da implementação.

---

# Article V — Test First

Toda funcionalidade relevante deve possuir teste automatizado.

---

# Article VI — Stable Releases

Nenhuma release é criada sem:

- aplicação iniciando corretamente;
- testes principais aprovados;
- documentação atualizada.

---

# Article VII — Architecture

Toda dependência deve apontar para o domínio.

Presentation

↓

Application

↓

Services

↓

Repositories

↓

Domain

↓

Infrastructure

Nunca no sentido inverso.

---

# Article VIII — Technical Debt

Toda dívida técnica identificada deverá ser registrada.

Nenhuma dívida técnica será esquecida.

---

# Article IX — Continuous Refactoring

Refatorações pequenas e frequentes são preferíveis a grandes reescritas.

---

# Article X — Simplicity

A solução mais simples que atende aos requisitos deve ser preferida.