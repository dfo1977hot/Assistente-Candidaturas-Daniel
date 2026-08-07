# Coverage Governance

## Meta e baseline

O objetivo arquitetural permanece cobertura global de pelo menos 85%, incluindo
branch coverage. O baseline aprovado esta em `quality/coverage-baseline.json` e
e uma protecao contra regressao da divida historica, nao uma nova meta maxima.

Milestones globais: 70% -> 75% -> 80% -> 85%. Eles sao metas de evolucao. O
baseline e independente: representa o melhor resultado validado e protege o
projeto contra regressao entre milestones.

## Quality Gates

Fast Quality Gate, para desenvolvimento continuo:

```powershell
.\scripts\quality_gate.ps1 -Gate Fast -Tests tests\application\composition\test_context_services.py
```

Ele executa Ruff, compileall e os testes direcionados informados.

Full Quality Gate, periodico ou antes de release:

```powershell
.\scripts\quality_gate.ps1 -Gate Full
```

Ele executa a suite completa com coverage e branch coverage, gera
`.coverage-full.json` e bloqueia somente regressao abaixo do baseline. A meta
de 85% continua configurada no `pyproject.toml`; ela nao foi reduzida.

## Codigo novo ou modificado

Codigo novo ou modificado deve buscar pelo menos 85% quando a cobertura de diff
for mensuravel no ambiente de CI. Esta Sprint nao adiciona dependencias para
diff coverage: a verificacao deve usar uma ferramenta consolidada no pipeline
quando a CI disponibilizar um diff confiavel da base de comparacao.

## Atualizacao do baseline

Somente uma execucao aprovada do Full Quality Gate pode atualizar
`quality/coverage-baseline.json`. Quando a cobertura global ou de branches
superar seu valor registrado, o gate promove essa metrica automaticamente. O
baseline nunca diminui; resultados inferiores continuam bloqueados pela regra
de nao regressao. Milestones nao condicionam a promocao.

Exemplo: um Full Gate valido de 69,74% promove o baseline global de 68,15%
para 69,74%, mesmo antes do milestone de 70%. Um resultado posterior de 69,00%
e bloqueado, enquanto 70,18% promove o baseline e tambem registra o milestone.

## Anti-gaming

Nao reduza o threshold, remova modulos do source, adicione `omit` ou
`pragma: no cover` sem justificativa revisada. Testes devem verificar resultados
e comportamentos observaveis; imports isolados, duplicacao artificial e asserts
vazios nao contam como evidencias de qualidade.

## Divida priorizada

Critico: componentes de Application/Infrastructure com muitos statements sem
cobertura, em especial `acd/application/job_description_analysis_service.py` e
repositorios legados.

Medio: motores e modelos de `acd/engineering/architecture` sem exercicio
direto de comportamento.

Baixo: widgets e paginas de Presentation sem fluxo funcional de alto risco.

## Coverage Recovery I (2026-07-24)

A recuperacao concentrou testes comportamentais em Application Analytics,
`JobProfileRepository`, `InterviewRepository` e `EvidenceAggregator`.

- Baseline inicial: 68,15% global e 48,42% de branches.
- Resultado medido: 69,74% global e 52,29% de branches, com 1.078 testes aprovados.
- Delta: +1,59 pontos percentuais globais e +3,87 pontos percentuais de branches.
- Milestone de 70%: nao atingido.

A suite completa e a geracao de `.coverage-full.json` foram concluídas, mas o
Full Quality Gate falhou posteriormente ao desserializar o relatorio JSON no
PowerShell. Por isso, o baseline permanece em 68,15% ate que a leitura do
relatorio seja corrigida e validada em uma execucao Full futura; nenhum valor
foi promovido nesta Sprint.

## Full Quality Gate Reliability (2026-07-24)

O relatorio de coverage.py e JSON valido, mas inclui chaves vazias em mapas de
funcoes e classes por arquivo. O Windows PowerShell 5.1 nao consegue converter
essas chaves em propriedades por meio de `ConvertFrom-Json`, mesmo que as
metricas agregadas sejam validas. O comportamento anterior transformava essa
falha de parsing em uma comparacao contra `0%`.

O gate agora delega a leitura do relatorio completo a `scripts/coverage_report.py`.
O parser usa a biblioteca padrao do Python, valida o arquivo e as metricas
obrigatorias, preserva `0%` quando ele e real e retorna apenas um payload plano
para o PowerShell. Erros de leitura ou estrutura encerram o gate explicitamente
como `Coverage report parsing failed`; eles nunca sao convertidos em metricas.

Os testes isolados validam JSON valido, invalido, inexistente e incompleto,
coverage global e de branches, `0%` real e comparacoes com baseline. O Full
Gate desta Sprint executou a suite uma unica vez, mas parou antes do parsing
porque um teste de repositorio dependente de horario cruzou o limite de dia.
O teste foi estabilizado com dados de calendario explicitos e validado de forma
direcionada. Como a suite completa nao pode ser repetida nesta Sprint, o
baseline permanece inalterado.

## Validacao final do Full Quality Gate (2026-07-25)

O Full Quality Gate corrigido concluiu em fluxo completo no Windows PowerShell
5.1. A suite teve 1.086 testes aprovados e 53 warnings preexistentes. O parser
Python processou o relatorio gerado pelo coverage.py e o PowerShell recebeu as
metricas planas corretamente.

- Coverage global validado: 69,74437237695535%.
- Coverage de branches validado: 52,29124236252546%.
- Regra de nao regressao: aprovada contra o baseline global de 68,15%.
- Milestone de 70%: nao atingido; gap de 0,25562762304465 ponto percentual.
- Baseline: mantido, pois o milestone ainda nao foi ultrapassado.

## Coverage Recovery II (2026-07-25)

A recuperacao foi limitada ao comportamento observavel de
`ApplicationRepository`, um repositorio de Infrastructure com uso por servicos
e adaptadores de consulta. Nenhum modulo de producao foi alterado.

- Full Quality Gate: aprovado, com 1.088 testes aprovados.
- Coverage global: 70,02416380516343% (anterior: 69,74437237695535%).
- Coverage de branches: 52,80040733197556% (anterior: 52,29124236252546%).
- Milestone de 70%: atingido por 0,02416380516343 ponto percentual.
- Baseline monotono: promovido automaticamente para as duas metricas.
