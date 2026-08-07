# Resume Optimization Workflow

`ResumeOptimizationWorkflow.execute(application_id)` prepares a read-only
optimization context. It uses `ApplicationContextService` to obtain the
associated `curriculum_id`, then uses `ResumeContextService` to read the
curriculum and latest persisted ATS result.

The workflow returns explicit availability for an unknown application, missing
curriculum, missing ATS, missing vacancy description, or ready persisted context. Gaps and recommendations
are returned only as persisted ATS data; their absence remains `None` and is
not interpreted as an empty result.

No ATS comparison, gap analysis, recommendation engine, AI provider, rewrite,
or persistence is performed. Existing resume versioning remains untouched.

The workflow is read-only. Only `ResumeOptimizationUseCase` turns a ready
preparation into an explicit generation command.
