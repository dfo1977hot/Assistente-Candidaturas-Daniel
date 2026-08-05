# Candidate Decision Workflow

## Objetivo

`CandidateDecisionUseCase` e o ponto de entrada unico para consumidores que
precisam de uma decisao sobre uma candidatura persistida.

## Fluxo

`execute(application_id)` delega ao `CandidateDecisionService`. O servico ja
usa `InterviewContextService` para compor os Contexts necessarios e retorna
`CandidateDecisionResult` imutavel.

## Responsabilidades e dependencias

O caso de uso apenas orquestra e nao conhece Query Adapters, repositorios,
Infrastructure, ATS ou Presentation. No runtime desktop, ele e instanciado
explicitamente por `DesktopCompositionRoot`; o registrador legado permanece
restrito a compatibilidade e testes isolados conforme ADR-029.

## Contrato e limitacoes

O unico parametro e `application_id`; a cada chamada a decisao reflete os
Contexts atuais. Nao ha cache nem persistencia de decisoes. Candidaturas
inexistentes ou evidencias incompletas retornam o resultado explicavel
`INSUFFICIENT_DATA` produzido pelo servico de decisao.
