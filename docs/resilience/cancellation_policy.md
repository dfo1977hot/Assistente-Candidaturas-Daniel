# Cooperative cancellation policy

The sole Qt `LongRunningTaskExecutor` owns pending, running, cancelling,
cancelled, succeeded, failed and timed_out states. `cancel()` sets a thread-safe
token. Composed work checks it between safe stages and before commit.

Cancellation never kills a thread or interrupts SQLite inside a transaction.
It is acknowledged when the callable returns or raises at a cancellation point;
cleanup and teardown still run. Late completion after cancellation or timeout
cannot become success. Shutdown requests cancellation and waits only for its
owner-defined bound.
