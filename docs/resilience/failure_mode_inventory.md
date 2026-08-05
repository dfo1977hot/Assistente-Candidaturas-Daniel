# Failure mode inventory

| Component | Operation | Failure | Impact | Recoverable? | Idempotent? | Policy |
|---|---|---|---|---|---|---|
| OpenAI | typed generation | timeout, rate limit, connection, 5xx | optional generation unavailable | transient only | yes before accepted output | bounded retry and deadline |
| OpenAI | typed generation | authentication, bad input, invalid schema | request rejected | no automatic retry | yes | safe typed result |
| Qt executor | background task | cancellation or deadline | operation incomplete | restart as new operation | operation-specific | cooperative token; suppress late result |
| SQLite | online backup copy | busy/locked | backup delayed | yes | yes to temporary destination | three short attempts |
| SQLite | validate | malformed or missing schema | integrity unavailable | no | yes | reject without destination mutation |
| Filesystem | write/promote | permission, capacity, I/O | artifact incomplete | operator action | conditional | delete partial; preserve source |
| Restore | validate/copy/replace | hash, integrity, schema, replace | restore rejected | controlled manual retry | no automatic replay | validate; safety backup; atomic promotion |
| Plugin | load/init/shutdown | invalid contract, import/runtime error | optional capability unavailable | manual after correction | unknown | disable plugin; preserve runtime |
| Logging | file handler creation | permission/I/O | file diagnostics unavailable | yes | yes | console-only degradation |
| Desktop | bootstrap | invariant failure | cannot safely start | no | no | fatal; log and propagate |

Official categories are transient, permanent, cancelled, timeout, resource
unavailable, invalid data, state conflict, integrity, permission, capacity,
external dependency and fatal.
