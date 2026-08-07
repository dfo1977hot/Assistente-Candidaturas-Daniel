# Local state inventory

Inventory taken 2026-08-04 by names, sizes and timestamps only. Personal record
contents were not read or reproduced.

| Path or pattern | Type | Consumer | Real/test | Sensitive | Versionable | Policy |
|---|---|---|---|---|---|---|
| `data/database/acd.db` (798,720 bytes) | SQLite, tracked legacy path | desktop | real local | yes | no | preserve in place; never test/package; future reviewed untracking |
| `data/database/acd_backup_before_refactor_20260701_203814.db` (753,664 bytes) | historical backup | unknown/manual | backup | likely | no | retain; do not open/delete automatically |
| `*.db-wal`, `*.db-shm`, `*.db-journal`, `*.journal` | SQLite transaction state | SQLite | runtime/temp | yes | no | never copy/delete while active; exclude from Git/wheel |
| pytest `tmp_path` databases | temporary SQLite | tests | test | synthetic | no | exclusive external basetemp; dispose connections |
| `tests/fixtures/database.py` | fixture factory | pytest | test | synthetic | yes | must never resolve the real path |
| `data/automation/screenshots/*` | local automation evidence | automation/user | real local | likely | no | preserve locally; do not enumerate content in reports |
| `data/curriculos`, `data/cartas`, exports and attachments | user documents | desktop/user | real local | yes | no | local only; explicit retention |
| `.coverage*`, caches and Gate artifacts | generated diagnostics | development | temporary | low/paths | no | local only; governed summaries may be versioned |
| JSON under source/docs/tests | schemas/config/test fixtures | runtime/tests | mixed | review | sometimes | version only reviewed deterministic resources |

No WAL, SHM or journal file was found during the initial snapshot. No active
Python, pytest or SQLite process was visible. The two database files above are
classified without content queries; table counts were intentionally not taken
from the real or historical files.
