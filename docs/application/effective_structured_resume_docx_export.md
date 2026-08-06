# Exportação DOCX do currículo efetivo estruturado

`ExportEffectiveStructuredResumeDocxUseCase` recebe apenas `application_id` e
`destination_path`. Ele reutiliza `EffectiveApplicationResumeUseCase` para
resolver a fonte ORIGINAL ou RESUME_VERSION efetivamente adotada e entrega
somente o `StructuredResumeSnapshot` à porta `StructuredResumeDocxExportPort`.

O resultado é imutável e informa status, origem, identificadores e destino. A
operação é read-only para o domínio: não cria versões, não adota currículo, não
executa ATS e não gera conteúdo. A única escrita é o arquivo DOCX autorizado.
