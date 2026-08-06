# Resume Version Adoption

The Application Layer exposes two explicit commands: `AdoptResumeVersionRequest`
selects an existing generated version, while `UseOriginalResumeRequest` clears the
selection. Their use cases return `ResumeAdoptionResult` with either `ORIGINAL` or
`RESUME_VERSION` as a derived source.

Adoption validates that the application exists, has a base `curriculum_id`, and
that the requested version appears in the generated versions for that curriculum.
Repeated adoption of the same version performs no write. Returning to the original
curriculum is also idempotent.

These operations change only `selected_resume_version_id`. They do not overwrite
curriculum or version content, create versions, execute ATS or AI, or expose UI.
Presentation integration remains deferred to Resume Intelligence VI-B.
