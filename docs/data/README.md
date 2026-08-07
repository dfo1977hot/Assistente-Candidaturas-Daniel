# Data lifecycle governance

This area governs local state without exposing its contents. The official path
policy, backup/restore policy, schema compatibility and migration policy are
separate contracts. Operations must use explicit paths, synthetic test data and
the SQLite online-backup API. The real database is never a test fixture.

Operational procedure: `../operations/database_backup_restore.md`.
