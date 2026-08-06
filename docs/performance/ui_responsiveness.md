# UI responsiveness

The event loop must not perform network, backup/restore or blocking sleep directly. Long operations use the sole productive `LongRunningTaskExecutor`, which owns one `QThread`, supports cooperative cancellation and rejects concurrent work instead of accumulating a queue.

Sprint K verifies widget construction, event processing during active work, cancellation-request latency below 250 ms and completion. Progress coalescing was not added because the executor exposes lifecycle signals, not high-frequency progress. A future progress producer must bound/coalesce updates before Presentation.

