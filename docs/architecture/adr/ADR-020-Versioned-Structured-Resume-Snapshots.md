# ADR-020 — Versioned Structured Resume Snapshots

## Status

Accepted.

## Context

`Curriculum.description` and `ResumeVersion.content` are textual records. They cannot safely be converted into a professional document structure by parsing, nor can a generated version be silently merged with its original curriculum.

## Decision

Each source may optionally persist an independent schema-v1 JSON snapshot in nullable `TEXT` columns: `curricula.structured_content_json` and `resume_versions.structured_content_json`. The Application codec validates the payload and serializes deterministic JSON before a repository persists it. Query adapters expose immutable models and an explicit availability status.

`NULL` means structured content is unavailable. Legacy text stays readable. Invalid and unsupported stored payloads preserve the textual preview while reporting `INVALID` or `UNSUPPORTED_SCHEMA`; they are never repaired automatically.

## Consequences

No heuristic backfill, cross-source merge, AI structured generation, or DOCX export is introduced. Future generation must explicitly emit and validate a supported snapshot before persistence. Future export can require `AVAILABLE` structure while leaving legacy textual preview intact.
