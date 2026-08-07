# Performance governance

Sprint K establishes measured local performance governance without turning workstation speed into a product contract. Stable invariants are blocking; volatile timings use deliberately tolerant ceilings. Executable checks live in `tests/performance` and architectural boundaries in `tests/architecture/test_performance_boundaries.py`.

This area owns startup, UI responsiveness, capacity, query-count, resource and synthetic boundary evidence. It never authorizes real network calls, real plugins, or operations on the user's database.

- `performance_inventory.md`: critical paths and ownership.
- `performance_budgets.md`: measurements, budgets and enforcement.
- `capacity_limits.md`: queues, volume and backpressure.
- `benchmark_methodology.md`: reproducible method.
- `query_performance.md`: query-count and index decisions.
- `memory_governance.md`: resource lifecycle.
- `ui_responsiveness.md`: event-loop contract.
- `performance_test_matrix.md`: evidence matrix.

