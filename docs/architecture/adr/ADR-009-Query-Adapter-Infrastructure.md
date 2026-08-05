# ADR-009 - Query Adapter Infrastructure

## Status

Aceito

## Data

2026-07-23

## Contexto

A camada Application possui Query Ports e DTOs para compor leituras sem expor
modelos de persistencia. Os adaptadores de candidatura, curriculo, empresa e
vaga ja existiam, mas os historicos de ATS e de entrevista ainda nao possuíam
implementacoes concretas.

## Decisao

Adotar adaptadores de Infrastructure por porta de consulta. `ATSHistoryQueryAdapter`
consulta somente o historico persistido de ATS e retorna o registro mais recente
para um curriculo. `InterviewQueryAdapter` consulta somente entrevistas
persistidas associadas a uma candidatura. Ambos retornam exclusivamente os DTOs
definidos em `acd.application.query_ports`.

## Responsabilidades

Os adapters traduzem dados de repositorios existentes para contratos de leitura
da Application. Eles nao executam analises ATS, nao realizam preparacao de
entrevistas, nao criam regras de negocio e nao acessam Presentation.

## Alternativas avaliadas

1. Expor os repositorios de Infrastructure diretamente a Application.
2. Duplicar consultas em novos servicos de dominio.
3. Implementar adaptadores para os Query Ports existentes.

Foi escolhida a alternativa 3 para preservar a inversao de dependencias,
reutilizar os repositorios atuais e manter os modelos de persistencia fora da
camada Application.

## Impactos e limitacoes

Os adaptadores dependem das capacidades de leitura atuais dos repositorios. O
historico de ATS retorna somente a entrada mais recente por curriculo, conforme
o contrato atual. As entrevistas sao filtradas a partir da colecao retornada
pelo repositorio existente. Nenhum registro de Dependency Injection foi criado
nesta sprint.

## Estrategia futura

Registrar os adaptadores no ponto de composicao quando uma funcionalidade da
Application necessitar injeta-los. Evoluir os Query Ports apenas quando novos
casos de uso de leitura exigirem consultas adicionais.
