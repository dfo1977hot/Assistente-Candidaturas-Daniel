# ADR-007 - Pipeline History Persistence

## Status

Aceito

## Data

2026-07-23

## Contexto

O IAP precisa fornecer histórico para recuperação e futuras consultas, sem
acoplar a Presentation à Infrastructure.

## Alternativas avaliadas

1. Histórico apenas em memória.
2. Reutilizar `WorkflowExecution`.
3. Persistir execução própria do IAP via port e adaptador SQLite.

## Decisão

Adotar a alternativa 3. `PipelineExecution` representa o histórico do IAP;
Application depende do port e Infrastructure implementa SQLite.

## Impactos

Cria uma tabela dedicada e retenção configurável por quantidade de registros.
Dashboard permanece fora desta decisão.

## Estratégia futura

Adicionar adaptadores de armazenamento e consultas para Dashboard sem alterar
os casos de uso da Application.
