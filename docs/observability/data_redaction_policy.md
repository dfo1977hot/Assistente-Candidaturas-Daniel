# Data redaction policy

Structured fields use an allowlist. Free text is defensively redacted for
synthetic or accidental CPF, RG, email, telephone, passwords, API keys, bearer
tokens, authorization/cookie headers, connection URLs and prompt/response or
resume content fields. Secret-like keys always become `[REDACTED]`; long values
are truncated. Paths are reduced to non-personal labels for diagnostics.

Redaction operates on copies and never mutates domain objects. Hashing is used
only for stable technical identifiers when necessary, never to make secrets
safe for logging.
