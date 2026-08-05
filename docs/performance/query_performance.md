# Query performance

The critical application-list query uses `joinedload` for company and job. `before_cursor_execute` instrumentation proves that loading and dereferencing 50 applications executes exactly one SQL statement, preventing N+1 behavior.

Existing job indexes cover company, status and application date. No index was added: representative local volume did not demonstrate a bottleneck, and an unproven index adds write cost. Search/filter and pagination require representative volume, `EXPLAIN` evidence and stable UX semantics before change.

