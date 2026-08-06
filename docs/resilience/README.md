# Resilience governance

Sprint J defines finite recovery at the boundaries where failure is expected:
OpenAI, SQLite lifecycle, filesystem promotion, plugins and the single Qt
long-running executor. `acd.resilience` owns the small shared vocabulary for
failure categories, outcomes, retry, deadlines and cooperative cancellation.

Integrity and security never degrade. A transient failure may be retried only
when the operation is explicitly idempotent. Permanent errors stop immediately.
Cancellation, timeout, failure and degradation are distinct states.

Circuit breaking is deferred: ACD has one optional low-volume provider and no
concurrent request scheduler. Durable checkpoints are also deferred; the
existing pipeline checkpoint remains in-memory and Sprint J adds no persistence.
