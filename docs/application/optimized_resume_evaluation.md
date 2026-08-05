# Optimized Resume Evaluation

`OptimizedResumeEvaluationUseCase` avalia explicitamente uma `ResumeVersion` no contexto da candidatura informada. A requisição imutável contém somente `application_id` e `resume_version_id`.

O caso de uso resolve o currículo com `ApplicationContextService`, restringe a busca da versão ao `curriculum_id` associado, lê o ATS original com `ResumeContextService` e usa as competências estruturadas da vaga obtidas por `VacancyQueryPort`. O conteúdo enviado ao `ATSEvaluator` é exclusivamente o da versão gerada.

O resultado é transitório (`persisted=False`): compara o score calculado da versão com o score original persistido e expõe delta, estado numérico, gaps e recomendações disponíveis. Não chama `ATSService.compare_curriculum()`, não reavalia o currículo original e não grava `ATSScore`, detalhes, gaps, recomendações ou histórico.

Limitação: a avaliação depende de competências estruturadas no perfil da vaga. Sem elas, o caso de uso retorna `vacancy_required`; ele não interpreta descrição livre nem inventa requisitos. Como a avaliação não é persistida, ela deixa de estar disponível quando o contexto visual é encerrado.
