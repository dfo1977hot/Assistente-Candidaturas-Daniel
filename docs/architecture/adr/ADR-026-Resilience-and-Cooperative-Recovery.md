# ADR-026: Resilience and Cooperative Recovery

## Status

Accepted

## Context

External AI, SQLite lifecycle, plugins and Qt background work had different or
implicit handling for retry, timeout and recovery. SDK retries were hidden and
task cancellation had no explicit state.

## Decision

Use dependency-free `acd.resilience` contracts for official failure categories,
finite idempotent retry, deadline and cooperative cancellation. OpenAI disables
SDK retries and applies ACD classification. SQLite retries only busy/locked
during safe online copy. The sole Qt executor owns explicit terminal states and
suppresses late completion after cancellation or timeout. Backup/restore rely on
validation, cleanup, safety backup and atomic promotion; plugin failure disables
only that capability.

Do not introduce a circuit breaker, durable checkpoint store, second executor
or general framework. In-process plugin timeout remains unenforceable without
process isolation.

## Consequences

Retries are bounded, observable, cancellable and forbidden for undeclared
non-idempotent work. Timeout and cancellation remain distinct. Integrity and
security never degrade. Tests use only deterministic local failure injection.
