# ADR-015 - Candidate Decision Support

## Status

Accepted; composition detail superseded by ADR-029

## Contexto

O ACD ja disponibiliza dados de candidatura por Query Ports, Query Adapters e
servicos de composicao. Faltava uma decisao funcional, explicavel e testavel
sobre a conveniencia de prosseguir com uma candidatura, sem recriar o motor
ATS, a analise de gaps ou mecanismos de recomendacao.

## Decisao

Adicionar `CandidateDecisionService` na camada Application. O servico depende
de `InterviewContextService` e retorna `CandidateDecisionResult` imutavel. A
politica usa exclusivamente score ATS persistido, gaps persistidos e
completude dos Contexts. No runtime desktop, o
`DesktopCompositionRoot` instancia explicitamente os Query Adapters, Contexts,
servico, caso de uso e ViewModel. O `DependencyContainer` historico permanece
somente para compatibilidade e testes isolados, conforme ADR-029.

## Consequencias

Application continua independente de Infrastructure e Presentation. A ausencia
de dados gera `INSUFFICIENT_DATA` ou confidence menor, sem reduzir a avaliacao
do candidato. Recomendacoes ATS sao apenas reutilizadas; nao ha nova execucao
de ATS, IA ou Gap Analysis.

## Alternativas avaliadas

1. Reutilizar `StrategyEngine` do Planner.
2. Acrescentar regras ao `RecommendationEngine` analitico.
3. Compor os Contexts existentes em um servico de decisao da Application.

Foi escolhida a alternativa 3 porque as duas primeiras possuem responsabilidades
distintas e dependencias de Infrastructure incompatíveis com este caso de uso.

## Estrategia futura

Futuros consumidores, como Dashboard e agentes, devem usar o resultado
imutavel. Novos sinais so podem ser adicionados depois de serem persistidos e
expostos pelos contratos de composicao existentes.
