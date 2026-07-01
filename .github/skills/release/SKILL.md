---
name: release
description: "Executa ciclo de release do ACD com validacao de gates, checklist, notas de versao e rastreabilidade."
argument-hint: "Versao alvo e tipo de release"
user-invocable: true
disable-model-invocation: false
---

# Release

## Pre-condicoes
- Quality gates aprovados.
- Checklist de release completo.

## Procedimento
1. Confirmar versao e changelog.
2. Validar migrations e backup.
3. Gerar artefatos de release.
4. Publicar release notes.
