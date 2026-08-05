# Resume Version Review

`ResumeVersionReviewUseCase` oferece uma leitura somente de versões geradas de um currículo associado a uma candidatura.

O caso de uso obtém a candidatura por `ApplicationContextService`, usa seu `curriculum_id` para carregar o conteúdo original por `ResumeContextService` e lista versões por `GeneratedResumeVersionQueryPort`. A seleção é validada contra a lista retornada para o mesmo currículo. Sem seleção explícita, a última versão retornada pelo port é exibida inicialmente de forma determinística.

Não há vínculo persistente entre `ResumeVersion` e `application_id` ou `vacancy_id`. Portanto, o histórico representa versões deste currículo, e duas candidaturas associadas ao mesmo `curriculum_id` exibem o mesmo histórico. Não é possível afirmar qual versão foi gerada para uma candidatura específica.

O fluxo não executa IA, ATS, Gap Analysis, Recommendation Engine ou qualquer escrita.
