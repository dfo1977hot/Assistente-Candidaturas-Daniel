# Memory and resource governance

The suite repeatedly constructs/destroys `ApplicationPage`, flushes deferred Qt deletion, collects garbage and compares `tracemalloc` snapshots. The coarse retained-growth ceiling is 8 MiB for ten cycles. Root logging handlers must remain unchanged and no owned worker may remain active.

Temporary engines are disposed, sessions use context managers, SQL listeners are removed, fake clients are closed, plugins shut down and Qt workers finish cooperatively. `tracemalloc` sees Python allocations only; native resources are governed primarily through ownership and teardown assertions.

