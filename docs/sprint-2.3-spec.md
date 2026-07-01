# Sprint 2.3 — Módulo de Candidaturas

## Visão geral

A Sprint 2.3 implementa o módulo central do ACD: o gerenciamento completo de candidaturas. O objetivo é permitir acompanhar o ciclo de vida de cada processo seletivo, desde a descoberta da vaga até a contratação ou encerramento, com histórico, follow-ups, timeline e indicadores básicos no dashboard.

## Objetivos de negócio

- Registrar candidaturas.
- Associar candidatura a empresa e vaga.
- Acompanhar o status do processo.
- Registrar feedback, entrevistas e follow-ups.
- Manter histórico da candidatura.
- Expor indicadores básicos no dashboard.

## Arquitetura obrigatória

- Clean Architecture
- SOLID
- Repository Pattern
- Service Layer
- SQLAlchemy ORM
- SQLite
- PySide6
- Type hints
- Docstrings

## Estrutura prevista

- acd/domain/entities/application.py
- acd/domain/entities/timeline_event.py
- acd/infrastructure/repositories/application_repository.py
- acd/services/application_service.py
- acd/presentation/pages/application_page.py

## Modelo de dados

### Application

- id
- company_id
- job_id
- curriculum_id (opcional)
- cover_letter_id (opcional)
- status
- application_date
- last_update
- next_follow_up
- response_date
- interview_date
- salary_expected
- salary_offered
- application_channel
- recruiter_name
- recruiter_email
- recruiter_phone
- feedback
- notes
- created_at
- updated_at

### TimelineEvent

- id
- application_id
- event_type
- description
- created_at

## Pipeline de status

O fluxo principal é:

Rascunho -> Preparando Currículo -> Preparando Carta -> Pronta para Aplicação -> Aplicada -> Em Triagem -> Entrevista RH -> Teste -> Entrevista Técnica -> Entrevista Gestor -> Oferta -> Contratada

Fluxos alternativos:

- Aplicada -> Rejeitada
- Entrevista RH -> Encerrada

Transições inválidas devem gerar exceção de domínio.

## Regras de negócio

- A candidatura deve ser criada com empresa e vaga obrigatórias.
- O status deve seguir a máquina de estados.
- A timeline deve registrar eventos automaticamente.
- Follow-ups devem poder ser registrados para acompanhamento futuro.
- O dashboard deve exibir o total de candidaturas.

## Interface

A página de candidaturas deve suportar:

- cadastro e edição
- pesquisa por empresa, vaga e recrutador
- filtros por status, empresa e canal
- tabela resumo
- timeline da candidatura

## Testes

Os testes devem cobrir:

- criação e atualização de candidaturas
- mudança de status
- timeline e eventos
- estatísticas básicas
