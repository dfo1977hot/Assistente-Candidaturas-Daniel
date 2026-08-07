# ADR-024: Observability and Local Diagnostics

## Status

Accepted

## Context

The desktop application had scattered logger construction, an import-time
`basicConfig`, a service-owned file handler and operational messages that could
carry user-provided values. There was no single policy for correlation,
redaction, rotation, health checks or support exports.

## Decision

`acd.observability` is the productive observability boundary. The desktop entry
point explicitly configures and closes logging; imports remain side-effect
free. Records are JSON Lines with stable event names, UTC timestamps, severity,
component, correlation/operation context and monotonic duration where relevant.

All structured values pass through centralized sanitization before emission.
Credentials and common personal identifiers are redacted, values are bounded,
and operational events prefer technical identifiers to business content. Logs
are local only, rotate by size, and degrade to console-only operation when the
per-user log directory is unavailable.

Diagnostics expose configuration labels, directory accessibility, Python and
application versions, and optional read-only SQLite integrity/table metadata.
They never expose records, secrets, absolute paths or mutate the database.
Support export requires an explicit new destination, writes deterministic JSON,
and returns a SHA-256 digest.

Audit persistence remains distinct from diagnostic logging. Its metadata is
sanitized at the application boundary and must not be used as a general event
dump.

## Consequences

- Presentation code does not own handlers or logging configuration.
- Correlation uses `contextvars`, so concurrent operations do not share mutable
  context.
- Startup, bootstrap, backup, restore and background-task events have a common
  local schema.
- No external telemetry, automatic support upload or global exception hook is
  introduced. Desktop and task boundaries retain exception ownership to avoid
  duplicate reporting.
- Log and diagnostic output are local runtime state and excluded from source
  control and built distributions.

