# Failure recovery runbook

1. Record the safe event, operation/correlation IDs, state and error class. Do
   not copy prompts, secrets, personal paths or database contents.
2. For cancellation, wait for acknowledgement and cleanup; never terminate a
   worker thread or process to force completion.
3. For OpenAI timeout/rate limit, allow only bounded automatic retry. After
   exhaustion preserve input and offer later manual retry. Fix authentication
   or invalid responses rather than retrying them.
4. For SQLite busy/locked, close competing ACD sessions and retry manually after
   exhaustion. Preserve malformed/integrity/schema evidence.
5. Never promote a failed backup. A failed restore keeps its destination and
   safety backup. Validate hash, integrity and schema before another attempt.
6. Disable a failed plugin. Do not repeatedly initialize it. In-process hangs
   require restart and future process isolation.
7. If file logging degrades, retain console diagnostics. Never weaken path or
   security validation to recover.
8. Audit manual retry, user cancellation, restore rollback, plugin disablement,
   resumed operation and selected fallback once per impactful action.
