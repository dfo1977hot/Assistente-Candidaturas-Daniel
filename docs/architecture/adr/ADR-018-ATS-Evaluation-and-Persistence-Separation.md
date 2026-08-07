# ADR-018 - ATS Evaluation and Persistence Separation

## Status

Accepted

## Context

`ATSService.compare_curriculum()` combined deterministic evaluation with persistence, preventing a safe future evaluation of textual resume versions.

## Decision

Introduce immutable Domain contracts `ATSEvaluationInput` and `ATSEvaluationResult`, orchestrated by `ATSEvaluator`. The legacy service adapts ORM entities to the input, invokes the pure calculation once, and persists its result through the existing repository.

## Consequences

Legacy persistence and return semantics remain compatible. Pure evaluation performs no writes and does not create an ATS history. No schema or version-to-score relationship is introduced.
