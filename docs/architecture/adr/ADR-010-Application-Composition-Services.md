# ADR-010 - Application Composition Services

## Status

Superseded for productive composition by ADR-029

## Data

2026-07-23

## Contexto

O ACD ja possui Query Ports, DTOs e adaptadores de Infrastructure para leituras.
Faltava uma camada da Application que montasse Contexts reutilizaveis sem expor
entidades de persistencia aos consumidores.

## Decisao

Adotar `ApplicationContextService`, `ResumeContextService` e
`InterviewContextService` na camada Application. Os servicos recebem somente
Query Ports e produzem Read Models imutaveis. O registro de adaptadores e
servicos ocorre no ponto de composicao de Infrastructure por meio do
`DependencyContainer`.

## Responsabilidades

Os servicos consultam dados existentes e montam Contexts. O adaptador de ATS
projeta somente a pontuacao historica que o contrato atual expoe. Nenhum
servico executa ATS, Gap Analysis, preparacao de entrevistas ou persistencia.

## Alternativas avaliadas

1. Permitir que servicos da Application consultem repositorios diretamente.
2. Adicionar a composicao aos servicos de dominio existentes.
3. Criar servicos de composicao dependentes de Query Ports.

Foi escolhida a alternativa 3 para preservar as fronteiras das camadas e
reutilizar os contratos de leitura existentes.

## Historical integration with Dependency Injection

`register_application_composition` associa cada Query Port ao seu Query Adapter
e registra os tres servicos por factories. O container resolve os contratos,
nunca classes concretas de adaptadores, para seus consumidores de
compatibilidade e testes isolados. O runtime desktop produtivo nao usa esse
registrador; ADR-029 governa a composicao explicita por
`DesktopCompositionRoot`.

## Limitacoes

Nao ha Query Port para resultados de Gap Analysis. Assim, `GapContext` nao e
inferido a partir da pontuacao ATS e permanece ausente. O registrador deve ser
chamado pelo ponto de inicializacao que possui as instancias dos repositorios.

## Estrategia futura

Adicionar novas composicoes somente quando houver casos de uso consumidores e
evoluir os contratos de leitura antes de expor novos dados persistidos.
