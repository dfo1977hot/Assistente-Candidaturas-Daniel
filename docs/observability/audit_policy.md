# Audit policy

Audit is explicit persisted evidence for state-impacting actions, separate from
debug and file logging. Its allowlisted fields are action, entity type,
technical identifier, UTC timestamp, outcome, source, correlation ID and
sanitized scalar metadata. User names, personal identifiers, content, secrets,
prompts, responses, headers and arbitrary object representations are omitted.

The existing `system_logs` table remains; Sprint H adds no ORM table. Candidate
creation/change/removal, workflow execution, backup, restore and relevant
configuration changes are eligible. UI navigation and read-only actions are not.
