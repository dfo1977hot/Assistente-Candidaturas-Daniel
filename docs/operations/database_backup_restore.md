# Database backup and restore runbook

1. Close the desktop application and confirm no Python/SQLite process is using
   the database.
2. Resolve the source through the official path policy; never assume CWD.
3. Choose a new local destination such as
   `acd-backup-YYYYMMDD-HHMMSS.sqlite3`; do not overwrite.
4. Invoke the lifecycle adapter so SQLite online backup, integrity validation,
   schema validation, SHA-256 and JSON metadata all complete.
5. Keep the database and its JSON manifest together and protect them as personal
   data. Retention/deletion is explicit; no automatic pruning currently exists.

Restore is a controlled operation, not a startup action. With the application
closed, validate the backup hash, integrity and schema; create and verify a
pre-restore safety backup; restore to a same-directory temporary file; validate;
then atomically replace. On failure retain the original and safety backup. Never
manually delete WAL/SHM/journal files, run a destructive migration, or restore
over the real database during tests. Sprint G validation uses temporary files only.
