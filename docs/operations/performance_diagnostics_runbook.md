# Performance diagnostics runbook

1. Record branch, commit, Python/Qt versions, hardware and cold/warm state.
2. Confirm no pytest/quality-gate process is active.
3. Run `tests/performance` with an exclusive workspace `--basetemp`; never use the real database.
4. Separate invariant failures from volatile timing failures.
5. Repeat timing outliers at least three times and compare median/range.
6. Inspect structured `performance.queue.saturated`, task and database durations without payloads or personal records.
7. Profile only a reproducible synthetic case; keep `.prof`, traces and outputs out of Git/wheel.

Never promote a performance baseline manually. A committed baseline requires a controlled runner, documented promoter and stable multi-run evidence. Never diagnose with real OpenAI, an installed plugin or the user's database.

