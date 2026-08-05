# ADR-027: Performance, Capacity and Responsiveness Governance

Status: Accepted

## Context

The desktop had functional startup, worker and data boundaries but no official measurement convention, capacity contract or regression budgets. Tight workstation timings would be unstable; implicit queue/query behavior would permit structural regressions.

## Decision

Use deterministic synthetic checks under `tests/performance`, `perf_counter` durations and coarse blocking ceilings. Statement count, queue capacity, resource ownership and absence of UI-thread blocking are hard invariants. The sole executor has capacity one and no backlog. Raw timing baselines remain informative until controlled CI proves stability.

Do not introduce cache, pagination, indexes, batching or concurrency without a measured bottleneck and compatible product contract. External boundaries use fake OpenAI and synthetic allowlisted plugins; SQLite uses temporary databases only.

## Consequences

Gross regressions fail without binding the product to one workstation. Query/backpressure behavior is explicit. Fine-grained comparison and pagination remain future work with evidence requirements.

