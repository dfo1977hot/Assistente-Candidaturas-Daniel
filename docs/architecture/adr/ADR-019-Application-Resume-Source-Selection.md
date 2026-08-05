# ADR-019 - Application Resume Source Selection

## Status

Accepted

## Context

An application has a base curriculum but can use a generated resume version for a
specific submission. Replacing curriculum content would lose the distinction and
couple selection to generation and ATS flows.

## Decision

Store a nullable `applications.selected_resume_version_id` foreign key to
`resume_versions.id`, with `ON DELETE RESTRICT` and an index. `NULL` means
`ORIGINAL`; an identifier means `RESUME_VERSION`. The source is derived, not
persisted. Application use cases validate the requested version within the base
curriculum's generated versions and write through an Application-safe port.

## Alternatives considered

Overwriting curriculum content was rejected because it destroys the original
source. A textual source column was rejected because it duplicates derivable state.
Selecting the latest version was rejected because selection must be explicit.

## Consequences

Existing applications keep `NULL` and remain compatible. There is no selection
history in this decision. Removing the column on rollback requires SQLite table
reconstruction and is not automated. UI support is deliberately deferred.
