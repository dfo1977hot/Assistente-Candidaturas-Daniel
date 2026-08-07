# Artifact Preservation Manifest

No artifact was moved or deleted. Future destination:
`.local/artifacts/quality-gates/<sprint>/` after a separate hash-verified
migration. The root inventory currently contains 205 `.sprint-*` files totaling
1,372,601 bytes.

## Final green Sprint C

| Path | Bytes | SHA-256 | Result |
|---|---:|---|---|
| `.sprint-c-pass-fix-full-gate-20260803-004606.exitcode.txt` | 1 | `5FECEB66FFC86F38D952786C6D696C79C2DBC239DD4E91B46729D73A27FB57E9` | exit 0 |
| `.sprint-c-pass-fix-full-gate-20260803-004606.metadata.json` | 346 | `2FD4607DF2055F275C935CD5AA1E11AA2AA471063AC4AC129A1691BDA038B66F` | metadata |
| `.sprint-c-pass-fix-full-gate-20260803-004606.stderr.log` | 2,819 | `CDE1CDED08E2E811E476546FED60D344E31740FA20112C112634941FB9DE158D` | evidence |
| `.sprint-c-pass-fix-full-gate-20260803-004606.stdout.log` | 51,355 | `676D06F16CADF2217429E81043A42A666F6B670C672E6EB3135C7409C8D21D77` | 1,302 passed |

## Final green Sprint D

| Path | Bytes | SHA-256 | Result |
|---|---:|---|---|
| `.sprint-d-coverage-recovery-full-gate-20260803-170037.exitcode.txt` | 3 | `13BF7B3039C63BF5A50491FA3CFD8EB4E699D1BA1436315AEF9CBE5711530354` | exit 0 |
| `.sprint-d-coverage-recovery-full-gate-20260803-170037.metadata.json` | 399 | `E85F69398B5797BAFF288B71A0F5FFAB0006C99FECF6871EE88065F3F4F451A5` | metadata |
| `.sprint-d-coverage-recovery-full-gate-20260803-170037.stdout.log` | 53,649 | `AC08B04098277DF253ACBE9C370BFD06AFA04799BC4402647F61B2A9C4EB519E` | 1,310 passed |
| `.sprint-d-coverage-recovery-full-gate-20260803-170037.stderr.log` | 2,774 | `6C9617690390BCACA62C5B0FBE5BA7D428DE2B2B0E1EAC25132C6D0CFF9393B3` | warnings |
| `.sprint-d-coverage-recovery-full-gate-20260803-170037.duration.txt` | 18 | `79313EFA08247E22515E2470926558C298B016EAA6DF45B9454E45B2FC8AEDA4` | duration |
| `.sprint-d-coverage-recovery-full-gate-20260803-170037.command.txt` | 98 | `98EEC9DA64F01D2CE0BD2132263AE4841DF859E831DAA901C625E0620D1B9209` | command |
| `.sprint-d-coverage-recovery-full-gate-20260803-170037.started-at.txt` | 35 | `8D7F51370D10FA9473ACEF72EDCA41A404EC30DB0EF76F3E1DD7CC84D677C3AA` | timestamp |
| `.sprint-d-coverage-recovery-full-gate-20260803-170037.gate.pid` | 7 | `0E77069C69D99E4A9E6F813CE0D0D9AF8A18D2E4330B6A1EA8B29C3726C59C4B` | historical PID |
| `.sprint-d-coverage-recovery-full-gate-20260803-170037.wrapper.pid` | 7 | `EBD21592DE3997B56D605F49B58A5077769FEA048DDAD3C7643F7F08C4A9F1E2` | historical PID |
| `.sprint-d-coverage-recovery-full-gate-20260803-170037.wrapper-entered.txt` | 76 | `9B955D62B61954BB178279F7C5B3AA0A02F4D6B6006402C36EF0F865743C2069` | wrapper evidence |
| `.sprint-d-coverage-recovery-full-gate-20260803-170037.wrapper-error.log` | 0 | `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` | empty |

Failed/interrupted attempts remain local for traceability and require a separate
retention decision.

## Sprint E evidence

| Sprint | Path or set | Type | Size | SHA-256 | Result | Preserve? |
|---|---|---|---:|---|---|---|
| E | `.sprint-e-full-gate-20260803-223046.*` | command, stdout/stderr, metadata, PIDs, duration, exit code | 56,460 bytes | retained locally; per-file hash required before a move | historical Gate evidence | Yes |
| E.0 | `quality/domain-sqlalchemy-baseline.json` | architectural baseline | 3,834 bytes | `4E16791651701BC9D72AEC4708BDD9EEC00D9D4931AB6E071542C92EFE184964` | 85-module allowlist, target zero | Yes, versionable |
| E.0 | `docs/architecture/adr/ADR-028-domain-orm-persistence-boundary.md` | decision record | 3,318 bytes | `D3C01A563FF54B47B81C1A2110C3A75202A392CD908DD1296C3897F13D32C5CE` | temporary exception accepted | Yes, versionable |
| E.0 | `tests/architecture/test_domain_sqlalchemy_dependencies.py` | governance test | 2,217 bytes | `75AE9A3BD520A6884D103AF61D4AF6610B93C3E82A104D12DA99A3C1527010AF` | growth blocked | Yes, versionable |

The historical C and D green sets above, failed attempts, wrappers, command
files, stdout, stderr, metadata, exit codes, and durations are all preserved.
No raw evidence is packaged or copied into a wheel.
