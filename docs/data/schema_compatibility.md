# Schema compatibility

The current authority is the explicit 92-table ORM manifest. This is a minimum
set, not a table count: extra tables are compatible and preserved; any missing
required table is incompatible. An empty database may be bootstrapped. A corrupt
database fails SQLite integrity validation. A database from a future version
with all required tables is readable only for backup/inspection; automatic
migration is not inferred.

There is no durable schema-version authority yet. The existing
`migration_history` domain table is not wired as one. A future version table or
Alembic adoption requires an ADR, an initial snapshot, upgrade ordering and
rollback/recovery tests. Until then, the manifest plus explicit guarded column
checks is the temporary compatibility mechanism.
