# Explicit Resume Optimization

The explicit persisted optimization flow starts only when a
`ResumeOptimizationRequest` is executed. The use case obtains the associated
curriculum, persisted ATS history, and vacancy context through
`ResumeOptimizationWorkflow`, then maps that already prepared data to the
existing `PromptContext` contract.

`ResumeGenerationService.generate_resume_from_context()` reuses the existing
prompt builder, AI provider, prompt persistence, and `ResumeVersion`
versioning. It does not invoke ATS, gap analysis, or recommendations.

The legacy `generate_resume()` flow remains unchanged in behavior: it builds
its own context and performs a new ATS comparison before generation.
