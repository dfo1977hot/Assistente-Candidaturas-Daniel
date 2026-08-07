# Validação de qualidade do currículo estruturado

A `ApplicationPage` expõe a ação **Validar qualidade do currículo**. O botão usa o tooltip: “Verifica integridade, completude, consistência e exportabilidade do currículo efetivo.”

O fluxo é `ApplicationPage → LongRunningTaskExecutor → StructuredResumeQualityValidationViewModel → ValidateEffectiveStructuredResumeQualityUseCase`. A tarefa é identificada por `structured_resume_quality_validation`; enquanto ativa, o botão mostra **Validando...** e impede nova ação incompatível.

O painel read-only apresenta mensagem, resumo, score, contagens e cada issue com severidade, seção, campo e recomendação. Resultados e falhas obsoletos são ignorados após a troca de candidatura. A operação não persiste resultado, não executa ATS, IA, provider, exportação, geração ou adoção.
