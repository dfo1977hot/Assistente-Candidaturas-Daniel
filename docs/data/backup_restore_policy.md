# SQLite backup and restore policy

`SQLiteDatabaseLifecycle` implements the application contract with explicit
paths. Backup uses SQLite's online-backup API, so committed WAL content is
included consistently. It writes a new `acd-backup-YYYYMMDD-HHMMSS.sqlite3`
style destination, refuses overwrite, runs `PRAGMA integrity_check`, checks the
92-table minimum, calculates SHA-256 and writes adjacent JSON metadata without
the source path or record contents.

Restore validates existence, optional hash, integrity and required tables. If
the destination exists it first creates a verified safety backup. It restores
through a same-directory temporary SQLite file, validates it, then uses atomic
replacement where the filesystem supports it. Failures leave the destination
unchanged and preserve the safety backup. Extra tables are compatible and
preserved; missing required tables and corrupt files are rejected.

Connections must be explicitly closed. WAL/SHM/journal files must never be
deleted from an active database or copied as a substitute for the backup API.
Backups contain personal data: retention and deletion are explicit user actions.
