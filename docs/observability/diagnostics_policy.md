# Diagnostics and health policy

Diagnostics are generated on demand and remain local. Allowed values include
application/Python/platform versions, architecture, entry point, sanitized path
labels, existence and size, expected/found table counts, SQLite quick check,
packaged resource availability and writable-directory checks. Database records,
environment dumps, secrets, logs, documents and full personal paths are excluded.

Export is deterministic JSON to an explicit new destination, refuses overwrite,
and returns SHA-256. Health states are `healthy`, `degraded`, `unhealthy` and
`unknown`, each with safe details and monotonic duration. Checks are one-shot,
not continuous monitoring.
