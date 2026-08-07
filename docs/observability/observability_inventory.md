# Observability inventory

Inventory measured on 2026-08-04 without reproducing log or user-record content.

| Component | Path | Use | Category | Data recorded | Risk | Decision |
|---|---|---|---|---|---|---|
| legacy root logger | `acd/core/logger.py` | import-time file config | technical | free text | CWD/import side effect | replace with official configuration |
| `StructuredLogger` | `acd/infrastructure/platform/logger.py` | timing and context | technical/operational | arbitrary message/metadata | mutable context, no redaction | delegate to official events |
| company CRUD logger | `acd/services/company_service.py` | separate file handler | audit-like | identifiers and company names | personal data, CWD, duplicate handler | remove concrete handler and names |
| `AuditService` | `application/platform/services/audit_service.py` | persisted `system_logs` | audit | user id, message, metadata | arbitrary metadata | sanitize and retain as separate audit contract |
| platform health registry | `infrastructure/platform/health_check_registry.py` | database/filesystem/memory | health | paths and exception text | path/secret disclosure | new sanitized diagnostics facade |
| pipeline/workflow observability | application/domain workflow modules | in-memory traces | operational | technical IDs and durations | inconsistent names | use stable event catalog on critical paths |
| Python module loggers | 16 logger declarations | technical | free text | mixed | no central formatter | route through `acd` hierarchy |
| productive `print()` | none | — | — | — | none | CLI tool prints remain allowed |
| `basicConfig()` | one in `acd/core/logger.py` | global configuration | technical | local file | heavy import side effect | prohibited outside official config |
| local `.log` files | repository root, `logs/`, `data/logs/` | historical/runtime | local artifacts | potentially sensitive | tracking/package/privacy | preserve; ignore; do not read automatically |

Known ignored exceptions exist in plugin discovery and source tooling; they are
catalogued debt and are not converted into observability success paths here.
