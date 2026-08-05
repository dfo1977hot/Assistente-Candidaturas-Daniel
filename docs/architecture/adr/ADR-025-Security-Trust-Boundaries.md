# ADR-025: Security and Trust Boundaries

## Status

Accepted

## Context

The desktop accepts local files and paths, optionally calls OpenAI and contains
a legacy in-process plugin loader. Environment reads, path validation and
external-content validation were dispersed or implicit. The loader could mutate
`sys.path`, import an arbitrary file and receive a live database session.

## Decision

`acd.security` is the shared technical boundary for secrets, canonical paths,
external-file structure, external HTTPS URLs, AI data envelopes and plugin
manifests. Runtime secrets come only from an allowlisted environment provider
called explicitly during composition. External content is bounded and validated
before filesystem or provider use.

Plugins remain disabled by default and execute only when a canonical trusted
root and explicit name allowlist are both supplied. Manifests and simple entry
points are strict, `sys.path` is not modified, and plugin context contains only
non-sensitive application version metadata. No database session, logger or
secret provider is exposed. Authorized plugins still run in-process and are not
sandboxed.

AI content is marked as untrusted data, bounded and submitted only through the
official typed adapter. Optional endpoints require credential-free external
HTTPS and SDK TLS defaults. Responses are strict-schema validated and never
used as commands, paths, modules, SQL or configuration.

## Consequences

- Path traversal, ambiguous Windows filenames and unsafe external-file
  structures fail with safe typed errors.
- Environment dumps and dispersed secret reads are prohibited by architecture
  tests.
- Existing local database compatibility remains; no migration or real data
  operation is introduced.
- OS ACL hardening, signed plugins, process isolation, encrypted secret storage,
  DNS rebinding prevention and dependency attestation remain residual work.

