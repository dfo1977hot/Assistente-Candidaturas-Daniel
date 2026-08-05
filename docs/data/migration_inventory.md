# Migration inventory

No migration was executed during Sprint G.

| Migration | Origin | Destination | Idempotent | Destructive | Consumer | Status |
|---|---|---|---|---|---|---|
| company missing columns | `create_database.py` | `companies` | guarded | no | productive bootstrap | legacy inline evolution |
| selected resume version column/index | `create_database.py` | `applications` | guarded | no | productive bootstrap | legacy inline evolution |
| structured JSON columns | `create_database.py` | curricula/resume versions | guarded, backup first | no | productive bootstrap | legacy inline evolution |
| datetime source rewrite | `scripts/migrate_datetime.py` | Python source | textual | potentially broad | developer only | not a DB migration |
| in-memory migration registry | `infrastructure/platform/migration_service.py` | supplied session | partial | downgrade undefined | no productive composition evidence | experimental |
| release migration records | `application/release/services/migration_service.py` | history record | no actual schema action | no | release subsystem | placeholder |
| `migration_history` ORM table | Registry manifest | local schema | create-only | no | release metadata | present; not schema authority |

Alembic configuration and a durable ordered schema migration history were not
found. `create_all()` remains bootstrap, not migration.
