# Princípios Arquiteturais do ACD

## Responsabilidade Única

Cada módulo deve possuir apenas uma responsabilidade.

---

## Domain First

Toda regra de negócio pertence ao domínio.

---

## Repository Pattern

A camada de apresentação nunca acessa diretamente o banco.

---

## Service Layer

Toda lógica passa pelos Services.

---

## Test First

Toda funcionalidade importante deve possuir teste.

---

## Documentation First

Alterações estruturais devem ser documentadas antes da implementação.

---

## Backward Compatibility

Sempre que possível, preservar compatibilidade durante migrações arquiteturais.

---

## Clean Architecture

Dependências sempre apontam para o domínio.

Presentation

↓

Services

↓

Repositories

↓

Domain

↓

Infrastructure