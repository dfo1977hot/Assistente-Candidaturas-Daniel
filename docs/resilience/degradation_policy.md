# Controlled degradation policy

AI, reviewed plugins, file diagnostics and optional backup availability may be
unavailable while safe local editing remains usable. Degradation is visible,
sanitized, and states what was preserved and whether manual retry is safe.

Authentication policy, path validation, hash, schema, SQLite integrity, restore
validation, TLS, secret handling and atomic promotion never degrade. There is no
fabricated AI fallback: preserve input and offer manual retry or non-AI mode.
A failed plugin is disabled; a failed file logger retains console logging.
