# Validação de qualidade do currículo estruturado

`ValidateEffectiveStructuredResumeQualityUseCase` resolve o currículo efetivo por `EffectiveApplicationResumeUseCase` e valida seu `StructuredResumeSnapshot` com `StructuredResumeQualityValidator`.

O request possui apenas `application_id`. Para `ORIGINAL`, valida o snapshot original; para `RESUME_VERSION`, valida exclusivamente a versão adotada persistida. A versão visualizada não participa da resolução.

O resultado expõe status funcional, origem, identificadores, score, validade, issues e contagens. A operação é read-only: não executa ATS, IA, provider, persistência, exportação, adoção ou geração. Conteúdo estruturado ausente e schema não suportado são retornados como status funcionais.
