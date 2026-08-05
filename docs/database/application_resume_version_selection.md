# Application Resume Version Selection

`applications.selected_resume_version_id` is a nullable `INTEGER` foreign key to
`resume_versions.id`. It records the generated resume version selected for one
application; it does not replace `applications.curriculum_id`.

`NULL` means the application uses its original curriculum. A non-null identifier
means it uses that specific resume version. The source is derived from this value
and is not stored separately.

New databases receive the column and index through the SQLAlchemy mapping.
Existing SQLite databases are evolved idempotently during `create_database()` with
`ALTER TABLE ... ADD COLUMN` only when the column is absent, followed by
`CREATE INDEX IF NOT EXISTS ix_applications_selected_resume_version_id`.

The foreign key uses `ON DELETE RESTRICT`. A selected version cannot be deleted
until the application selection is cleared. SQLite foreign-key enforcement is
provided by the central connection listener.

## Rollback and limitations

Rolling back application code does not remove this column or constraint. Removing
the column from SQLite requires a table reconstruction and is intentionally not
automatic. Back up the database before a downgrade; no automatic schema rollback
is provided.
