# Resume Optimization UI

`ApplicationPage` owns the selected `application_id` and exposes the explicit
**Otimizar currículo** action. Its injected `ResumeOptimizationViewModel`
maps Application results to a safe immutable view state. The page invokes that
view model through `LongRunningTaskExecutor` under ADR-017, disables duplicate
clicks while running, and updates widgets only from executor signals.

Loading a page, changing selection, navigation, and the Candidate Decision
action **Preparar currículo** never start optimization.
