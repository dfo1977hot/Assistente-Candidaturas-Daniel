# Non-destructive migration policy

Every future migration needs a unique ordered identifier, explicit source and
target schema compatibility, preconditions, a verified backup, transaction
boundaries, idempotent execution, before/after tests, data validation and a
documented rollback or recovery path. Logs contain identifiers and counts only.

Allowed patterns include adding tables, nullable columns and indexes, or staged
copy/backfill with the old representation preserved. Silent `DROP TABLE`,
`DROP COLUMN`, truncation, destructive rename and deletion of extra tables are
prohibited. Automatic execution is deferred until durable schema versioning and
recovery semantics exist. No migration runs merely because a module is imported.

Alembic is deferred: the project first needs a reviewed initial revision for the
existing 92-table schema and a transition plan from guarded inline evolutions.
