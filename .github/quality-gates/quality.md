# Quality Gate (Consolidado)

## Objetivo
Centralizar verificacao final antes de merge e release.

## Checklist
- Testes: PASS
- Arquitetura: PASS
- Lint: PASS
- Typing: PASS
- Documentacao: PASS
- Cobertura: PASS
- Performance: sem regressao critica
- Seguranca: sem alerta critico aberto
- Agent SDK: contrato e handoff validados
- ADR Validator: PASS para mudancas estruturais

## Resultado
- READY: fluxo pode continuar.
- BLOCKED: corrigir e revalidar.

## Regra sem excecao
Se houver mudanca estrutural sem ADR, status BLOCKED.
