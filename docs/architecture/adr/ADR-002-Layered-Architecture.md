# ADR-002

## Título

Arquitetura em Camadas

---

## Status

Aceito

---

## Contexto

Durante a recuperação da Sprint 0 foi identificada a necessidade de separar responsabilidades.

---

## Decisão

O projeto passa a adotar oficialmente as seguintes camadas:

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

Nenhuma dependência poderá ocorrer no sentido contrário.

---

## Consequências

- maior desacoplamento;
- facilidade para testes;
- manutenção simplificada.