# Initial threat model

## Assets and actors

Assets are the local database, applications, resumes, letters, attachments,
backups, credentials, API keys, prompts, AI responses, logs, diagnostics,
plugins and configuration. Actors are the local user, accidental/malicious
file or document author, plugin author, external AI/network provider, compromised
dependency and an attacker with access to the user's session or filesystem.

## Trust boundaries

A user -> UI; B UI -> Application; C Application -> Infrastructure; D process
-> filesystem; E process -> SQLite; F process -> external services; G process
-> OpenAI; H plugin files -> process; I imported files -> parsers/storage; J
backup -> restore; K application data -> logs/diagnostics; L environment ->
configuration/secrets.

## Threats and controls

| Threat | Impact / likelihood | Controls | Residual risk |
|---|---|---|---|
| Secret or personal-data leak | high / medium | centralized secret access, redaction, allowlisted diagnostics, synthetic tests | a third-party library may expose data outside ACD logging |
| Path traversal/local overwrite | high / medium | canonical authorized roots, filename rules, overwrite policy | TOCTOU remains possible if another local process can replace path components |
| Malicious imported file/ZIP/XML | high / medium | size, signature, extension, JSON/XML/ZIP structural checks; no execution/extraction | parsers may contain upstream vulnerabilities |
| Malicious plugin | critical / medium | feature disabled, trusted root, explicit allowlist, strict manifest and interface | authorized plugins execute in-process without a sandbox |
| Prompt injection/exfiltration | high / high | untrusted-data envelope, data minimization, no tools/commands, typed strict response | model output remains probabilistic |
| Backup tampering/corruption | high / medium | SHA-256, manifest, integrity/schema validation, safety backup | attacker controlling both file and manifest can replace both |
| Arbitrary execution/subprocess injection | critical / low | no productive subprocess/eval/exec/shell; architectural tests | developer-only scripts remain trusted local tools |
| Network/SSRF/TLS bypass | high / low | HTTPS policy, no credentials/local literals, SDK TLS defaults, bounded timeout/retries | DNS rebinding is not prevented by literal-host validation |
| Log injection | medium / medium | JSON encoding, control-character normalization, bounded IDs/payloads | third-party/root logging is outside ACD ownership |
| Compromised dependency | high / low | bounded direct versions, clean wheel, no new dependency | no offline vulnerability database/scanner is configured |

No absolute security is claimed. Process sandboxing, OS ACL hardening, signed
plugins, encrypted local secrets and dependency attestation remain future work.

