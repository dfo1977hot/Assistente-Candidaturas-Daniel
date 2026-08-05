# Database bootstrap governance

`acd.models.base.Base` is the sole productive metadata. `load_models()` loads
the explicit ORM manifest and verifies its 92-table contract. Importing the
registry alone does not load models.

`DatabaseBootstrap` is invoked by `create_database()` before the desktop root
constructs repositories. It calls the registry, runs `SchemaInitializer`, and
requires the physical schema to match the manifest exactly. It is idempotent
and promotes the SQLite `PRAGMA user_version` baseline used by the migration
policy.

For a new database, all 92 tables must be present. Existing extra tables are
reported as a schema mismatch and are never removed. `create_all()` creates
missing tables only; it is not a migration system and cannot evolve columns,
types, names, or data. Migration governance is delegated to
`acd.database.migration_runner.DatabaseMigrationRunner`, which owns future
non-destructive version transitions.

To add an ORM model: use `Base`, add its module and table to the registry
manifest, update bootstrap/process tests and repository coverage, then run the
quality gates.
