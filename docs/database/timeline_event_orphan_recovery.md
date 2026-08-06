# Timeline Event Orphan Recovery

## Violation

The existing SQLite database contained one `foreign_key_check` violation: a timeline event referenced an application that no longer existed. The event had no safe independent meaning, and no recoverable application was found in the available historical backup.

## Recovery

Before correction, a timestamped copy of the SQLite database was created in the local database backup directory. The recovery used one explicit transaction: it revalidated the sole orphan, deleted only that event, ran `PRAGMA foreign_key_check`, and committed only after the result was empty.

## Prevention

The official SQLite engine enables `PRAGMA foreign_keys = ON` on every new connection. Tests now apply the same central listener to temporary SQLite engines and verify that deleting an application with timeline events is rejected, preventing another orphan from being created.

## Limitations and rollback

The data correction is recoverable from the timestamped database backup. The foreign-key listener does not repair historical data; `foreign_key_check` must be run before later schema evolutions. This recovery does not change the timeline foreign-key policy or schema.
