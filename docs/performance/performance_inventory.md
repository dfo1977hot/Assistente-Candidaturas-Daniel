# Performance inventory

| Critical path | Owner | Control |
|---|---|---|
| `app.py -> acd.desktop` import | Desktop entry point | cold subprocess benchmark |
| `DesktopCompositionRoot.build()` | Composition root | temporary database benchmark |
| `DatabaseBootstrap.initialize()` | Database | 92-table assertion and timing |
| `Sidebar` / `ApplicationPage` construction | Presentation | offscreen Qt timing |
| long-running actions | `LongRunningTaskExecutor` | one slot, rejection and cancellation |
| application listing | `ApplicationRepository` | one-statement test at 50 rows |
| SQLite backup/restore | SQLite lifecycle | temporary 92-table database |
| OpenAI/plugins | Infrastructure adapters | fake client/synthetic allowlisted plugin |

No productive subprocess or download path was found. Configuration caching already has explicit invalidation. No broad cache, batch layer, eager preloading or parallelism was introduced because measurements did not prove a bottleneck.

