# Pure ATS Evaluation

The legacy `ATSService.compare_curriculum()` previously combined calculation and persistence. It now maps its ORM inputs into `ATSEvaluationInput`, executes `evaluate()`, persists the resulting ATS data, and returns the same public dictionary shape.

`ATSEvaluator.evaluate()` accepts text and immutable value objects only. It reuses the existing score, gap and recommendation engines and returns `ATSEvaluationResult`; it has no ORM, session, repository or write dependency.

The pure result is not an ATS history entry. Persistence remains exclusive to the legacy path and no schema, migration, `application_id` behavior or `resume_version_id` relationship is changed.
