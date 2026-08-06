# ADR-023: Local database path and SQLite lifecycle

Status: Accepted

## Context

The desktop database was source-tree-relative, imports created directories and
legacy backup/restore copied a live SQLite file. Installed packages, WAL mode
and recovery require an explicit lifecycle with very low tolerance for data loss.

## Decision

Use one side-effect-free resolver with explicit/environment overrides, retain an
existing legacy database without automatic movement, and otherwise use the
per-user data directory. Bootstrap alone creates the selected directory. Backup
and restore are application contracts implemented in Infrastructure through the
SQLite online-backup API, integrity/schema/hash validation, a pre-restore safety
backup and same-directory atomic replacement. Extra tables remain compatible.

The 92-table manifest is the temporary schema authority. Alembic and automatic
migration are deferred until an initial revision and recovery plan are reviewed.

## Consequences

Runtime and tests no longer depend on CWD. Existing user state remains in place.
Backups correctly include committed WAL data and are treated as sensitive local
files. Restore is never automatic and tests operate only on temporary databases.
