# Structured resume snapshot columns

`curricula.structured_content_json` and `resume_versions.structured_content_json` are nullable SQLite `TEXT` columns without a default. `NULL` means no structured content is available; it is not an empty JSON string.

`create_database()` adds missing columns with idempotent `ALTER TABLE ... ADD COLUMN` calls. Before a file-backed database is evolved, it creates a timestamped adjacent `.bak` copy. Existing values are not converted or overwritten.

A valid v1 value contains `schema_version: 1` and every envelope section. Invalid JSON, unknown structural fields, and unsupported schema versions remain in place for diagnostics, but query adapters retain the textual content and expose an explicit non-available status.
