# ADR-021 — Native Structured Output Provider Boundary

## Status

Accepted.

## Decision

Structured resume generation uses a dedicated Application port rather than the textual `AIProvider.generate_text` contract. A compatible provider must declare native JSON Schema and structured-resume support before it can be called.

The input requires an existing `StructuredResumeSnapshot`; text is never parsed into a snapshot. Provider responses expose an immutable `StructuredResumeSnapshot` or an explicit functional status, never raw provider payloads.

## Consequences

The current installation has no approved external SDK, so production composition receives an explicit unsupported implementation. The textual provider and its existing generation flow remain unchanged. A concrete adapter requires a later dependency and configuration authorization.
