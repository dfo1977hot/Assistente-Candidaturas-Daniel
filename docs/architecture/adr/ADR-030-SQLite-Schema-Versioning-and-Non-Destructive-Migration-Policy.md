# ADR-030: SQLite Schema Versioning and Non-Destructive Migration Policy

## Status

Accepted

## Context

The productive SQLite schema already preserves data and extra tables, but the
repository lacked a durable, explicit version contract for the on-disk schema.
Without one, future upgrades would remain implicit, difficult to audit, and easy
to mix with bootstrap-only behavior.

The current baseline is the 92-table Registry loaded by `DatabaseBootstrap`.
The application also keeps legacy schema-evolution helpers in `create_database.py`
for compatibility while the migration policy is introduced.

## Decision

1. SQLite `PRAGMA user_version` is the canonical schema version source.
2. Schema version `1` is the baseline for the current Registry-backed schema.
3. `DatabaseBootstrap` creates the baseline schema and must never drop tables.
4. Schema version `0` is accepted only when the full 92-table baseline is
   present, and it normalizes to baseline version `1`.
5. `DatabaseMigrationRunner` is the only approved path for future schema
   transitions.
6. Migrations are applied with per-migration rollback: a failing migration is
   restored from its own pre-migration backup while earlier successful
   migrations remain committed.
7. Migrations must be ordered, non-destructive, and backed by a pre-migration
   backup.
8. Restore must reject future-schema backups and must validate integrity before
   replacing the destination.
9. Extra tables are preserved and reported; they are never removed implicitly.
10. `drop_all()` is forbidden in productive paths.

## Consequences

- The on-disk database can be inspected and reasoned about with a single version
  integer.
- Backups now carry schema metadata, hash evidence, and integrity validation.
- Future migrations can be added without reintroducing destructive schema reset
  workflows.
- The current legacy compatibility helpers remain allowed until a dedicated
  migration sweep replaces them.

## Alternatives considered

1. Keep relying on table count as a proxy for schema state. Rejected: fragile and
   not auditable.
2. Adopt a new dependency for migrations immediately. Rejected: unnecessary for
   the current baseline.
3. Continue with bootstrap-only evolution and no durable version. Rejected:
   future recovery would remain implicit.
4. Use SQLite `user_version` with an explicit migration runner. Accepted.

## References

- `acd/database/database_bootstrap.py`
- `acd/database/create_database.py`
- `acd/database/migration_runner.py`
- `acd/database/schema_version.py`
- `acd/infrastructure/database/sqlite_lifecycle.py`
- `tests/database/test_schema_version_governance.py`
