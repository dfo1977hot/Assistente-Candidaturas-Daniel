# ACD - Sprint 0.3

## Versao
v0.2.0-alpha

## Titulo
CRUD & Persistence Validation

## Epic
Core Platform

## Objetivo
Transformar a interface validada na Sprint 0.2 em uma aplicacao funcional com CRUD e persistencia SQLite para entidades centrais.

## Estrategia de execucao
Implementacao incremental por lotes:
- 0.3A: Empresas
- 0.3B: Vagas
- 0.3C: Candidaturas
- 0.3D: Curriculos
- 0.3E: Cartas

## Escopo

### Modulo Empresas
- Cadastro, edicao, exclusao, pesquisa, ordenacao e persistencia.
- Campos minimos: nome, segmento, website, linkedin, cidade, estado, pais, porte, observacoes.

### Modulo Vagas
- Cadastro, edicao, exclusao, pesquisa, filtros e persistencia.

### Modulo Candidaturas
- Criacao, alteracao de status, associacao com empresa e vaga, datas importantes e persistencia.

### Modulo Curriculos
- Cadastro, associacao a candidatura, caminho de arquivo, versao, idioma e observacoes.

### Modulo Cartas
- Cadastro, associacao a candidatura, versionamento e observacoes.

## Banco de dados - validacao obrigatoria
- Integridade referencial
- Chaves estrangeiras
- Indices
- Constraints
- Exclusao em cascata quando aplicavel
- Unicidade quando aplicavel

## Testes
- Repositorios em `tests/repositories/`
- Banco em `tests/database/`
- Integracao em `tests/integration/`

Metas de cobertura desta sprint:
- Database: 95%
- Repositories: 90%
- Services: 85%

## Logging
Registrar inclusao, alteracao, exclusao e erros de persistencia em `logs/crud_validation.log`.

## Relatorio
Gerar e manter atualizado `docs/project/SPRINT0.3_REPORT.md`.

## Criterios de aceite da sprint completa
- CRUD funcional para Empresas, Vagas, Candidaturas, Curriculos e Cartas.
- Persistencia apos reinicio do aplicativo.
- Sem violacoes de integridade referencial.
- Testes automatizados passando.
- Relatorio da sprint atualizado.
