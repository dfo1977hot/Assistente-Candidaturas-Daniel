# Architecture Documentation

Este diretorio centraliza a documentacao arquitetural do ACD.

## Estrutura
- adr/: Architecture Decision Records.
- diagrams/: diagramas de arquitetura.
- decisions/: relatorios de inventario e decisoes operacionais.
- dependency-graph/: grafos de dependencia gerados.
- database/: documentacao de schema e persistencia.
- sequence/: fluxos de sequencia e inicializacao.
- deployment/: topologia e estrategia de deploy.
- roadmap/: planejamento de evolucao arquitetural.

## Regra de governanca
Toda mudanca estrutural deve gerar ou atualizar um ADR em adr/.

## Gate pre-sprint
Antes de qualquer sprint, execute a skill architecture-inventory.
Se o status for BLOCKED, interrompa a sprint e execute consolidacao arquitetural.
