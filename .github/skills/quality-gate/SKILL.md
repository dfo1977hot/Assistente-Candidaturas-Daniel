---
name: quality-gate
description: "Executa o quality gate consolidado do ACD validando testes, arquitetura, lint, typing, documentacao, cobertura, seguranca e sinal de performance antes de merge ou release."
argument-hint: "Escopo (pr, pre-release, full)"
user-invocable: true
disable-model-invocation: false
---

# Quality Gate

## Objetivo
Validar se uma mudanca pode seguir para merge ou release.

## Verificacoes
1. Testes: suite principal e integracao.
2. Arquitetura: Architecture Inventory aprovado.
3. Lint: ruff e black.
4. Typing: mypy.
5. Documentacao: ADR/README/changelog quando aplicavel.
6. Cobertura: politica por camada.
7. Seguranca: verificacoes basicas de dependencias e configuracoes.
8. Performance: sem regressao critica reportada.
9. Agent SDK: contrato e handoff validados pelos validadores.
10. ADR validator: mudanca estrutural sem ADR implica bloqueio.

## Resultado
- READY: pode seguir.
- BLOCKED: corrigir e reexecutar gate.

Regra sem excecao:
- Mudanca estrutural sem ADR: BLOCKED.

## Saida obrigatoria
Gerar relatorio em docs/architecture/decisions/quality-gate-report.md com:
- Data
- Escopo
- Resultado por verificacao
- Status final READY ou BLOCKED
