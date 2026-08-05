# Optimized Resume Evaluation UI

O `ResumeVersionReviewPanel` apresenta o botão explícito **Avaliar versão otimizada** somente quando existe uma versão selecionada e o ViewModel foi injetado. A seleção ou troca de versão atualiza somente a revisão read-only e limpa qualquer avaliação transitória anterior.

O `ApplicationPage` reutiliza o `LongRunningTaskExecutor` existente. No clique, ele captura `application_id` e `resume_version_id`; resultados que não correspondem mais à candidatura ou versão visual atual são ignorados. Durante a execução, o botão fica desabilitado e o painel informa que está avaliando.

Em sucesso, a UI mostra que se trata da avaliação atual da versão selecionada, os scores e o delta, e informa explicitamente que o resultado não foi salvo no histórico. Nenhuma avaliação é iniciada durante carregamento, seleção, troca de versão ou navegação.
