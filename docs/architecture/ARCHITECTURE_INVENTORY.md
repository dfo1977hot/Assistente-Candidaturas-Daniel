# ACD Architecture Inventory

Data da auditoria:

2026-07-04

---

# Estatísticas

Arquivos Python

346

Linhas de código

25.349

Pages

17

Services

38

Repositories

23

Entidades

94

Testes

28

---

# Camadas

## Presentation

Responsável pela interface gráfica.

Status

🟢 Estável

---

## Services

Responsável pelas regras de negócio.

Status

🟢 Estável

---

## Infrastructure

Persistência.

Status

🟢 Estável

---

## Domain

Entidades.

Status

🟢 Em auditoria

---

## Database

SQLite + SQLAlchemy

Status

🟢 Estável

---

# Dívidas Técnicas Conhecidas

- coexistência dos módulos `agent` e `agents`;
- ampliar cobertura de testes;
- revisar entidades sem repositórios dedicados.

---

# Próxima Auditoria

Sprint 0.5