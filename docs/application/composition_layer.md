# Application Composition Layer

## Arquitetura

Os servicos em `acd.application.composition` montam Read Models imutaveis para
consumidores da Application. Eles dependem exclusivamente dos Query Ports em
`acd.application.query_ports`; nenhum servico de composicao importa repositorios
ou adaptadores de Infrastructure.

O registrador `register_application_composition`, localizado em Infrastructure,
permanece como compatibilidade para testes isolados. O runtime desktop nao o
usa: `DesktopCompositionRoot` associa explicitamente cada Query Port ao
respectivo Query Adapter e injeta os servicos de contexto por construtor,
conforme ADR-029.

## Fluxo de composicao

```text
Application service
    -> Query Port
        -> Query Adapter (Infrastructure)
            -> Repository
    -> Read Model
```

`InterviewContextService` coordena os demais servicos para montar um
`InterviewContext`: candidatura, empresa, vaga, curriculo opcional, resultado
ATS persistido e historico de entrevistas. Os historicos sao projetados para
valores primitivos, incluindo datas ISO-8601, para manter a serializacao.

## Responsabilidades

- `ApplicationContextService`: candidatura e historico da candidatura.
- `ResumeContextService`: curriculo e pontuacao ATS persistida.
- `InterviewContextService`: contexto completo de leitura para entrevista.

Os servicos apenas projetam dados existentes. Eles nao executam ATS ou Gap
Analysis, nao persistem dados e nao implementam regras de negocio.

## Evolucao do contrato ATS

`ATSHistoryQueryPort` continua sendo o unico contrato de leitura para historico
ATS. Seu DTO agora pode expor, quando persistidos, versao do curriculo, vaga e
perfil relacionados, palavras-chave do perfil, detalhes de criterio, gaps e
recomendacoes. Campos sem registro persistido sao `None`.

`ResumeContextService` permanece compativel: ele continua utilizando apenas a
pontuacao historica para montar `ATSContext`. Resultados completos ficam
disponiveis para futuros consumidores de leitura, sem disparar uma nova analise.
Competencias encontradas permanecem indisponiveis porque o esquema atual nao as
persiste.

## Classificacao de consumidores ATS

- `ResumeAnalysisOrchestrator.analyze`: comando de nova analise. Mantem o uso
  de ATS e Recommendation Engine e nao consulta o historico como fallback.
- `InterviewContextService`: consumidor exclusivamente read-only. Ja obtem a
  pontuacao persistida por `ResumeContextService`.
- Nao ha consumidor de Presentation, relatorio ou tela que leia atualmente o
  resultado ATS persistido completo.

`ResumeContextService.get_persisted_ats_result` e a operacao de consulta para
esses futuros consumidores. Ela retorna a analise mais recente por curriculo,
conforme a politica de `ATSHistoryQueryPort`, ou `None` quando nao ha historico.
Essa leitura nao executa ATS, Gap Analysis ou geracao de recomendacoes.

## Separacao entre consulta e comando

Para consultar uma analise persistida, o consumidor recebe
`ResumeContextService` por injeção e chama `get_persisted_ats_result(curriculum_id)`. O
retorno e o `ATSHistoryQueryDTO` completo da analise mais recente por curriculo,
ou `None` quando nao ha historico. Campos sem persistencia, como competencias
encontradas, tambem permanecem `None`.

Para solicitar uma nova analise, o consumidor usa
`ResumeAnalysisOrchestrator.analyze`. Esse fluxo de comando continua calculando
score, gaps e recomendacoes com os servicos existentes. A consulta historica
nunca aciona esse fluxo e nao fornece fallback para uma nova analise solicitada.

`context` e `None` quando dados obrigatorios da candidatura, empresa ou vaga
nao estao disponiveis. O campo `gaps` permanece `None` enquanto nao existir um
Query Port para resultados de Gap Analysis persistidos.
