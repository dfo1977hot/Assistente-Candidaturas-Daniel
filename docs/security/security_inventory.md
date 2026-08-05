# Security inventory

| Component | Input | Trust boundary | Risk | Current controls | Sprint I action |
|---|---|---|---|---|---|
| OpenAI provider | environment, resume and vacancy data | environment/application -> OpenAI | secret leak, prompt injection, excessive disclosure | typed response, SDK timeout/retries, safe errors | centralized provider, bounded untrusted-content envelope, HTTPS base URL |
| Plugin loader | directory, JSON manifest, Python module | filesystem -> process | arbitrary code execution | interface check, feature flag disabled | trusted roots, explicit allowlist, strict names/manifest/entry point, fail closed |
| Curriculum import | filename, type, bytes | user/file -> filesystem | traversal, oversized/malicious file | SHA-256 after write | validate name, size, extension and signature before controlled write |
| DOCX export | destination path, structured content | application -> filesystem | arbitrary overwrite/path | temporary file and atomic replace | path policy documented; caller must authorize explicit export root |
| SQLite lifecycle | source, backup, restore paths | filesystem -> database | tampered backup, traversal, overwrite | integrity/schema/hash, safety backup, atomic replace | validate external filename/path semantics before lifecycle operation |
| Diagnostics | destination and local metadata | application -> support file | secret/path disclosure | allowlisted report, no records, overwrite refusal | recursive allowlist test and controlled destination policy |
| Logging/audit | free text and structured fields | all layers -> local evidence | injection and secret/PII leak | centralized redaction and bounds | strip control/newline injection and validate correlation IDs |
| Configuration provider | JSON file | filesystem -> settings | untrusted JSON/types | explicit provider | retain as legacy; arbitrary paths require caller authorization |
| Engineering/scripts | source paths and subprocesses | developer -> tools | local code/file mutation | non-runtime scope | documented exception; no untrusted runtime consumer |

Findings: no productive `shell=True`, `eval`, `exec`, pickle, unsafe YAML or
external XML parser was found. ZIP exists only as the DOCX container and is
validated without extraction. No web server or inbound HTTP endpoint exists.

