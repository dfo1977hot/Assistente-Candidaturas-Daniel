# ADR-011 - ATS Read Model Expansion

## Status

Aceito

## Data

2026-07-24

## Contexto

O contrato `ATSHistoryQueryPort` fornecia somente a pontuacao e metadados de
um score ATS. Consumidores de leitura que precisam avaliar uma analise ja
persistida tambem necessitam dos gaps, recomendacoes e detalhes de criterio,
sem executar novamente o ATS.

## Decisao

Evoluir o DTO existente de `ATSHistoryQueryPort`, sem criar uma nova porta. O
adapter de Infrastructure projeta os registros persistidos associados ao
`score_id`: detalhes de score, gaps, recomendacoes, versao do curriculo, vaga,
perfil e palavras-chave relacionadas.

## Justificativa

Manter a mesma porta preserva o contrato de leitura do historico e evita
duplicar a descoberta de uma analise ATS. Os novos campos possuem valores
padrao, preservando consumidores que usam somente os metadados originais.

## Beneficios

- leitura completa de uma analise persistida sem novos calculos;
- Application continua dependente apenas do Query Port;
- `ResumeContextService` e `InterviewContextService` mantem compatibilidade;
- DTOs imutaveis e serializaveis evitam exposicao de entidades ORM.

## Limitacoes

Competencias encontradas nao sao persistidas pelo esquema atual e retornam
`None`. Ausencia de detalhes, gaps ou recomendacoes tambem retorna `None`, sem
inferencias. O adapter nao altera nem substitui `ATSService`.

## Impactos

O adapter realiza consultas somente de leitura para as tabelas relacionadas ao
score. Nenhum repositorio, servico, comando ou componente de Presentation foi
alterado.
