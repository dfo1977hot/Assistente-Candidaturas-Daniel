# ADR-001

## Título

Governança Arquitetural do ACD

---

## Status

Aceito

---

## Data

2026-07-04

---

## Contexto

O projeto ACD ultrapassou 25 mil linhas de código, tornando necessária uma governança arquitetural formal.

---

## Decisão

Adotar uma arquitetura guiada por documentação.

Toda alteração estrutural deverá possuir:

- documentação;
- testes;
- validação funcional;
- registro em CHANGELOG.

---

## Consequências

Positivas

- maior rastreabilidade;
- menor dívida técnica;
- evolução controlada.

Negativas

- maior esforço inicial de documentação.