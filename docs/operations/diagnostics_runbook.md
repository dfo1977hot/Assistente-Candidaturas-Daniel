# Diagnostics runbook

Close sensitive workflows, choose a new explicit local JSON destination and run
the diagnostics exporter. Review the sanitized report before attaching it to a
support request. It contains no complete logs or database rows and is never sent
automatically. A refused overwrite protects previous evidence.

Health checks may open an explicitly selected SQLite file read-only for table
names and `quick_check`; never point tests at the real database. Close logging
handlers before deleting temporary logs on Windows. Retention deletion remains
an explicit user operation.
