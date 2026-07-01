---
name: sprint-implementation
description: "Implementa escopo funcional aprovado da sprint respeitando CONSTITUTION, ADLC, agentes e quality gates."
argument-hint: "Sprint e escopo aprovado"
user-invocable: true
disable-model-invocation: false
---

# Sprint Implementation

## Pre-condicoes
- Architecture Inventory APPROVED.
- ADR presente para mudanca estrutural.
- Handoff do Architecture Agent concluido.

## Procedimento
1. Implementar apenas escopo aprovado.
2. Nao violar limites de camada.
3. Executar testes e quality gate.
4. Atualizar documentacao necessaria.
