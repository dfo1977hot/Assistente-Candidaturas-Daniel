# Intelligent Application Pipeline

`IntelligentApplicationPipeline` é o orquestrador de Application para etapas
injetadas do fluxo de candidatura. Cada `PipelineStage` declara nome, executor e
habilitação. A execução retorna `PipelineStageResult` com status, resultado,
duração e diagnóstico.

Nesta primeira entrega, o pipeline não persiste estado, publica eventos ou
integra o Dashboard. Esses itens pertencem às etapas posteriores da Sprint.

`PipelineState` concentra o estado transitório de uma execução: progresso,
etapa atual, tempo decorrido, erros, warnings, resultados parciais e checkpoint
em memória. Persistência e retomada serão adicionadas em tarefas posteriores.

Os eventos `PipelineStarted`, `StageStarted`, `StageCompleted`, `StageFailed`,
`PipelineCompleted` e `PipelineCancelled` são contratos auditáveis do Kernel:
todos carregam identificador de execução, payload e timestamp UTC.

`PipelineDiagnostics` consolida duração total e por etapa, falhas, warnings,
regras aplicadas, serviços usados e resultado final sem modificar a execução.

`PipelineRecovery` valida o checkpoint em memória e retoma a execução da próxima
etapa registrada, sem reiniciar etapas anteriores.

`PipelineProgress` expõe percentual, etapa atual, tempo decorrido, estimativa,
tempo restante e mensagens para consumidores internos, sem depender de UI.

`PipelineObservability` gera um identificador de execução e mantém trace e
métricas em memória. Logs e telemetria são emitidos exclusivamente por callbacks
injetáveis, preservando a independência da camada Application.
