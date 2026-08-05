# Benchmark methodology

1. Use the project venv and an exclusive workspace `--basetemp`.
2. Measure with `time.perf_counter()` and report milliseconds.
3. Run cold imports in fresh subprocesses with isolated CWD and explicit project `PYTHONPATH`.
4. Prefer medians; retain ranges when variance matters.
5. Create temporary SQLite databases and validate all 92 ORM tables.
6. Run Qt offscreen, pump the event loop and close widgets/workers.
7. Inject a fake OpenAI client and use a synthetic allowlisted plugin.
8. Assert SQL statement count rather than optimizer wall time.

Budgets fail only on stable coarse regressions. No network, real database, personal data, installed plugin, real backup or restore participates.

