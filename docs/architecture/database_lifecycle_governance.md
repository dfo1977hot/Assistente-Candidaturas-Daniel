# Database Lifecycle Governance

## Official contract

- Canonical resolver: `acd.database.local_state.resolve_database_path()`
- Canonical productive directory: `%LOCALAPPDATA%\ACD\data\acd.db`
- Legacy compatibility path: `data/database/acd.db`
- Import-time side effects are forbidden.
- Tests must use explicit overrides and a non-productive path guard.
- Schema version `0` is treated as a legacy baseline only after validating the
  full 92-table registry.

## Lifecycle

1. Resolve the path without touching the filesystem.
2. Create parent directories only during explicit bootstrap.
3. Open the database through `create_database()`.
4. Record schema version with `PRAGMA user_version`.
5. Promote schema only through non-destructive migrations.
6. Create backups with the SQLite backup API.
7. Validate backup integrity and hash before restore.
8. Reject future-schema backups during restore.
9. Keep extra tables intact.

## Backup policy

- Backup destination must be unique.
- Metadata must include schema version, checksum, size, and application version.
- WAL content must be captured through the online backup API.
- Backups are local evidence and are not packaged.

## Migration policy

- `DatabaseBootstrap` owns the baseline schema creation.
- `DatabaseMigrationRunner` owns future version transitions and rolls back only
  the failing migration, preserving earlier successful migrations.
- During rollback, the runner may widen the restore ceiling to its supported
  schema version so it can restore the just-created pre-migration backup.
- `drop_all()` is prohibited in productive paths.
- Schema versions must advance monotonically.
- Failed migrations must restore from a pre-migration backup when possible.

## Recovery policy

- Corrupt backups are rejected.
- Future schema backups may be created for evidence, but restore rejects them.
- Current or older schema backups can be restored if the integrity check passes.
- A restore must never overwrite the only copy without a safety backup.

## Related references

- [ADR-023](./adr/ADR-023-Local-Database-Lifecycle.md)
- [ADR-030](./adr/ADR-030-SQLite-Schema-Versioning-and-Non-Destructive-Migration-Policy.md)
- [database path policy](../data/database_path_policy.md)
