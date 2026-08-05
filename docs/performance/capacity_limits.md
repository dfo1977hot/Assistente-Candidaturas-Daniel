# Capacity and backpressure

`LongRunningTaskExecutor` has one active slot and no backlog. `queue_capacity == 1`; while occupied, `queue_depth == 1` and another submission is rejected immediately with `performance.queue.saturated`. This prevents hidden memory growth and duplicate work.

The application list was verified with 50 synthetic rows in one SQL statement, including company and job access. The current contract returns the complete list; pagination is not introduced without a demonstrated volume and UI contract. Higher volumes must first define ordering, navigation and compatibility. Security-owned input/file limits remain authoritative; Sprint K adds no competing byte limits or unbounded standard queue.

