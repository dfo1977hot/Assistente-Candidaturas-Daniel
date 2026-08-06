# Database path policy

`acd.database.local_state.resolve_database_path()` is the only official
resolver. It is absolute and independent of the current working directory.
Precedence is:

1. explicit argument (tests and controlled tools);
2. `ACD_DATABASE_PATH` configuration;
3. existing legacy `data/database/acd.db` for compatibility;
4. `%LOCALAPPDATA%/ACD/data/acd.db` (portable fallback:
   `~/.local/share/ACD/data/acd.db`).

Resolution has no filesystem side effect. `create_database()` creates only the
selected parent directory during explicit bootstrap. Imports do not create a
database or directories. The existing legacy database is not moved, duplicated
or rewritten by path resolution; a future migration requires user action,
backup, verification and rollback.
