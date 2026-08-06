# ADR-012 - Persisted ATS Result Integration

## Status

Aceito

## Data

2026-07-24

## Contexto

O resultado ATS persistido completo passou a estar disponivel em
`ATSHistoryQueryPort`, mas `ResumeContextService` expunha somente uma projecao
resumida de pontuacao. Era necessario permitir consultas completas sem
substituir o fluxo que executa novas analises.

## Decisao

Adicionar `ResumeContextService.get_persisted_ats_result`, que delega ao
`ATSHistoryQueryPort` e retorna o DTO imutavel ja existente. A operacao segue a
politica atual de retornar a analise mais recente por curriculo ou `None` quando
nao ha historico. `ResumeAnalysisOrchestrator.analyze` permanece o unico fluxo
de comando para novas analises.

## Consumidores analisados

- `ResumeAnalysisOrchestrator.analyze`: comando de nova analise, nao migrado.
- `InterviewContextService`: leitura por `ResumeContextService`, mantida.
- Nenhum consumidor de Presentation ou relatorio elegivel foi encontrado.

## Alternativas rejeitadas

1. Usar historico como fallback silencioso para uma nova analise.
2. Duplicar o DTO ATS em um novo modelo de leitura.
3. Expor adaptadores ou repositorios a consumidores da Application.

As alternativas violariam a separacao comando-consulta, duplicariam contratos
ou quebrariam as fronteiras de camada.

## Beneficios e consequencias

Consumidores read-only podem acessar uma analise completa sem chamar ATS, Gap
Analysis ou Recommendation Engine. A compatibilidade da projecao resumida e do
orquestrador e preservada. Nenhuma dependencia de DI adicional foi necessaria.

## Limitacoes

Nao ha competencia encontrada persistida; o campo permanece `None`. Nao foram
adicionados paginacao, comparacao historica ou selecao manual de versoes.
