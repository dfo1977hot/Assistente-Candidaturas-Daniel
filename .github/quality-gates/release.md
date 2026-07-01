# Release Gate

## Objetivo
Evitar publicacao de versao com riscos nao controlados.

## Pre-condicoes
- Architecture Gate PASS.
- Testing Gate PASS.
- Coverage Gate PASS.
- Documentacao de release atualizada.

## Regra
Se qualquer gate estiver FAIL ou BLOCKED, release proibida.
