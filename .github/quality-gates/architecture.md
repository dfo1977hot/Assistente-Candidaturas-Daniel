# Architecture Gate

## Objetivo
Bloquear merge e sprint quando houver degradacao arquitetural.

## Checklist obrigatorio
- Sem duplicacoes criticas de modulos e camadas.
- Sem imports circulares bloqueantes.
- Base unica SQLAlchemy.
- Engine unico.
- SessionLocal unica.
- ADR atualizado para mudanca estrutural.
- Architecture Inventory com status APPROVED.

## Regra
Se qualquer item falhar, status BLOCKED.
