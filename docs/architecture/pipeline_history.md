# Pipeline History Persistence

O histórico do IAP é persistido em `pipeline_executions`. A Application depende
do port `PipelineExecutionHistoryPort`; a Infrastructure fornece o adaptador
SQLite. Cada registro inclui identificador, versão, status, duração, etapas,
falhas, warnings, diagnóstico e resumo serializados em JSON.

A retenção é configurável por `retention_limit` no `PipelineHistoryService`.
Após cada registro, execuções excedentes são removidas pelo adaptador.
