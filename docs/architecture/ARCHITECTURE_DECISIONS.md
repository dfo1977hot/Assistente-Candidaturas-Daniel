# ADR-001

## Título

Consolidação da Arquitetura de Agentes

## Data

2026-07-04

## Contexto

O projeto possuía duas arquiteturas paralelas (`agent` e `agents`), gerando conflitos de mapeamento ORM.

## Decisão

Adotar exclusivamente a arquitetura `acd.domain.agents` como padrão para novas funcionalidades.

## Consequências

- Elimina conflitos de MetaData.
- Simplifica os testes.
- Reduz a dívida técnica.
- Facilita a manutenção futura.