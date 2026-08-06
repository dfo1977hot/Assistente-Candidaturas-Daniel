# Retry policy

Retries are centralized in `acd.resilience.policy.execute_with_retry`. A policy
has finite attempts, bounded exponential backoff and jitter, a total deadline,
injected clock/sleeper seams, cancellation checks, and an explicitly idempotent
operation.

OpenAI retries timeout, rate limit, connection errors and provider 5xx only.
Authentication, bad request, invalid response/schema and cancellation are not
retried. SQLite lifecycle retries only `busy/locked`, for three short attempts.

No automatic retry is permitted for invalid credentials/input/path/hash/schema,
unauthorized plugins, restore promotion, non-idempotent mutation without a key,
or confirmed permanent failure. Scheduled retries are sanitized technical events.
