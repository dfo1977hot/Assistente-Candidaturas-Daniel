# Deterministic failure test matrix

| Component | Failure injected | Expected result | Retry | Rollback | Final state |
|---|---|---|---|---|---|
| Retry core | transient N times | bounded recovery | yes | n/a | succeeded |
| Retry core | permanent | original error | no | n/a | failed |
| Retry core | deadline | safe timeout | stops | n/a | timed_out |
| Qt task | cancellation | late result suppressed | no | task-owned | cancelled |
| Qt task | deadline | cooperative cancellation | no | task-owned | timed_out |
| OpenAI fake | rate limit/timeout | bounded retry or typed failure | transient only | no local effect | recovered/failed |
| OpenAI fake | invalid response | typed invalid response | no | no local effect | failed |
| SQLite fake | busy/locked | three short attempts | yes | partial removed | recovered/failed |
| Backup temp | validation/write failure | source preserved, partial removed | manual | cleanup | failed |
| Restore temp | replace failure | original preserved | no | safety retained | rolled_back |
| Plugin synthetic | invalid/import/init | plugin disabled | no | capability omitted | degraded |
| Shutdown/task | active task | cancellation and bounded wait | no | cleanup | cancelled/incomplete |

Tests use doubles, injected clocks/sleepers, temporary databases and synthetic
plugins. No real network, database, ACL, disk pressure or plugin is used.
