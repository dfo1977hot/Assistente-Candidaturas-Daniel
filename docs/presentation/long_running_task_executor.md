# Long-Running Task Executor

`LongRunningTaskExecutor` runs one parameterless callable in a `QThread` and
returns its unmodified result through Qt signals. It is Presentation-only and
does not know business use cases, infrastructure, or widgets. A single
instance rejects a second start until its active task finishes, then can be
reused.

The executor retains its worker and thread until `QThread.finished`, then
releases both references and emits `finished`. Widgets must subscribe to its
signals in the UI thread; workers never access widgets. There is intentionally
no cancellation, progress reporting, retry, or generic timeout.
