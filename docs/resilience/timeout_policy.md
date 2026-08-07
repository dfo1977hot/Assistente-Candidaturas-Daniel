# Timeout policy

- OpenAI uses a positive configured operation timeout, 30 seconds by default.
  It bounds the SDK call and the total ACD deadline.
- SQLite uses an explicit short connection busy timeout; only `busy/locked` is retried.
- Qt tasks accept an optional positive deadline. Expiry requests cooperative
  cancellation and suppresses late success; it never terminates a thread.
- Shutdown cancellation and waiting must be bounded by the composing owner.
- Backup/restore and local file validation have no invented wall-clock timeout:
  they use temporary files, atomic boundaries and safe cancellation points.
- Plugins execute in-process, so safe enforcement of an execution timeout
  requires future process isolation.

Timeout is distinct from user cancellation and emits `operation.timed_out`.
