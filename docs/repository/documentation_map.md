# Documentation Map

| Area | Category | Status | Index/action |
|---|---|---|---|
| `docs/architecture/` | architecture, ADRs, debt, runtime, database | official/evolving | [architecture index](../architecture/README.md) and ADR index |
| `docs/architecture/adr/ADR-028-*` | persistence-boundary decision | official | retain with monotonic ORM baseline and decoupling plan |
| `docs/development/` | developer and packaging guidance | active | retain in place |
| `docs/operations/`, `docs/observability/`, `docs/security/`, `docs/resilience/` | operations | active | retain topical runbooks and policies |
| `docs/repository/` | repository governance | official | this directory indexes local-state policies and manifests |
| `docs/project/`, `docs/releases/`, `docs/release/`, sprint specifications | history/release | mixed | preserve; review before retirement |
| `.github/CONSTITUTION.md`, `.github/ADLC.md`, quality gates | governance | official | authoritative project governance |
| feature topical directories | feature documentation | mixed | classify incrementally; no bulk move |

Duplicates, stale documents, and documents without a direct reference are not
automatically obsolete. Retirement requires a consumer, historical-value, and
compatibility review.
