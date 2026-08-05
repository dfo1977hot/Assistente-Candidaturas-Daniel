# ADR-017: Presentation Long-Running Task Execution

## Context

Long-running desktop operations must not block the Qt UI thread.

## Decision

Use `LongRunningTaskExecutor`, implemented with one `QThread` and one worker
`QObject` per submitted callable. Results and exceptions return through Qt
signals. A single executor rejects concurrent execution and can be reused after
completion.

## Alternatives considered

- Synchronous execution: rejected because it freezes the UI.
- `QRunnable` with `QThreadPool`: rejected because a shared pool adds lifecycle
  management not needed for one independently owned callable.
- `ThreadPoolExecutor`: rejected because it is not Qt-native for signal and
  object lifecycle handling.
- `asyncio`: rejected because the application has no integrated asyncio event
  loop.

## Rules

Workers do not access `QWidget` instances. Widgets update only after receiving
signals on the UI thread. The executor remains domain-agnostic and does not
use a Service Locator. Cancellation, progress, retries, and generic timeouts
are out of scope.
