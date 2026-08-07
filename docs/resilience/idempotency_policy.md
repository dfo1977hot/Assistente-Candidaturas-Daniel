# Idempotency policy

| Operation | Classification | Replay rule |
|---|---|---|
| OpenAI generation before accepted output | idempotent for local effects | bounded retry; never accept partial output |
| SQLite backup to new temporary destination | source-idempotent | cleanup partial before a new operation |
| Integrity/hash/schema validation | naturally idempotent | safe to repeat |
| Restore | non-idempotent external effect | no automatic retry; promote once |
| Application create/update | non-idempotent without operation key | no generic retry |
| Workflow stage | operation-specific/unknown | handler declares semantics |
| Resume persistence | idempotent only with operation/version identity | no hidden persistence |
| Export to new destination | idempotent while destination is absent | refuse overwrite |
| Audit append | non-idempotent | audit final impactful action once |
| Plugin action | unknown | no automatic retry |

Sprint J introduces no deduplication table. Existing operation IDs and version
identities remain the replay keys until a real duplicate failure justifies more.
