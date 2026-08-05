# Structured logging policy

`acd.observability.logging_config` is the sole configuration point. Imports do
not create directories or handlers. Explicit startup configures the `acd`
logger with optional console output and UTF-8 JSON Lines in
`%LOCALAPPDATA%/ACD/logs` (or an explicit test override). File logs rotate at
5 MiB with five retained files. Shutdown closes and removes owned handlers.

Every event contains timestamp, level, logger, event name, message,
correlation/operation IDs, component, status, application version, process ID
and thread. Optional duration uses `perf_counter()`. Configuration is
idempotent and does not alter third-party root handlers.

DEBUG is non-sensitive internal detail; INFO is normal operation; WARNING is a
degraded fallback; ERROR is an incomplete recoverable operation; CRITICAL is an
unusable or inconsistent state. Logging never changes functional results.
