# Secrets policy

The process environment, accessed only through `acd.security.secret_provider`,
is the current official runtime source. `.env` is local, ignored and is not
loaded by production code; `.env.example` contains names and safe empty/default
non-secret values only. Secrets have no application default.

Secret names are explicitly allowlisted. Values are read on explicit
composition/configuration, never on module import, and are validated for
presence, length and control characters. Tests inject synthetic mappings.
Missing optional secrets disable the integration; invalid required values raise
a safe typed error. Rotation/revocation occurs at the provider and requires a
process restart. ACD never writes a secret to Git, wheel, SQLite, log, audit,
diagnostic, UI or user-facing traceback. Redaction is defense in depth, not an
authorization mechanism.

