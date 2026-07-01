# Testing Gate

## Objetivo
Permitir merge apenas com qualidade funcional comprovada.

## Regra
- Executar pytest completo.
- Falha em teste critico bloqueia merge.
- Falha em integracao bloqueia merge.

## Resultado
- PASS: merge permitido.
- FAIL: merge bloqueado.
