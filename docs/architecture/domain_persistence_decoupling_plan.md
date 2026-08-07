# Domain persistence decoupling plan

## Scope and invariant

ADR-028 records a temporary exception for the 85 SQLAlchemy-bound modules
listed exactly in `quality/domain-sqlalchemy-baseline.json`. That file is the
machine-checked module inventory. All 85 are registered through the explicit
ORM Registry and map the current 92-table manifest; none may be moved or
changed during Sprint E.

| Module group | Class/table scope | Coupling | Consumers | Registry ORM | Migration risk |
| --- | --- | --- | --- | --- | --- |
| `domain/agent/*.py` (5) | `AgentGoal`, `ExecutionPlan`, `PlanTask`, `ReasoningStep`, `ToolCall`; five tables | ORM model | legacy agent repositories/services | Yes | High: foreign keys and legacy compatibility |
| `domain/agents/*.py` (7) | Agent, capability, memory, message, session, task, tool; seven tables | ORM model with enums | multi-agent repositories/services | Yes | High: `agent`/`agents` naming overlap |
| `domain/career/*.py` (5) | career goals, recommendations, plans, milestones, gaps; five tables | ORM model | career services/repository | Yes | Medium |
| `domain/connector/*.py` (6) | connector profiles/rules/history/mapping/platform/schema; six tables | ORM model | connector services/repository | Yes | Medium: mapping and serialization |
| `domain/entities/*.py` (46) | applications, curricula, resumes, workflows, ATS, automation, profile, and related tables | ORM entity mapping | application services and infrastructure repositories | Yes | High: relationships, serialization, and primary workflows |
| `domain/learning/*.py` (5) | hypotheses, insights, records, outcomes, patterns; five tables | ORM model with enums/JSON | learning repository/services | Yes | Medium: enum/JSON persistence |
| `domain/platform/*.py` (6) | backup, configuration, health, logs, metrics, status; six tables | ORM model with JSON/enums | platform services/repository | Yes | Medium |
| `domain/release/*.py` (5) | documentation, installed versions, migrations, releases, update history; six tables | ORM model with enums | release services/repository | Yes | Medium: compatibility and audit history |

The matrix is intentionally grouped by bounded context; the baseline is the
authoritative, alphabetized one-row-per-module list and is validated by
`tests/architecture/test_domain_sqlalchemy_dependencies.py`.

## Wave 1 - Simple models

Start with isolated tables with no relationship graph or critical
serialization. For each candidate, create a persistence model, a pure domain
type, and a tested mapper without changing table names. Candidate selection
requires evidence from the Registry and repository consumers.

Acceptance: unchanged table set, mapper round-trip tests, no added baseline
entry, and targeted repository tests green.

## Wave 2 - Applications and curricula

Migrate `domain/entities` application, curriculum, resume, education,
experience, and version models with their repositories and mappers. These are
high-risk due to relationships and product serialization.

Acceptance: application flows and repository contracts preserve behavior; the
Registry still reports the same 92 tables.

## Wave 3 - Agents and memory

Consolidate the boundary design for `domain/agent` and `domain/agents` before
extracting persistence mappings. Do not duplicate mappers or rename tables.

Acceptance: explicit compatibility adapters, agent and multi-agent repository
tests green, and no table/serialization name changes.

## Wave 4 - Platform, release, connector, learning, and career

Migrate one bounded context at a time, beginning with the least-connected
context selected by consumer analysis. Preserve JSON, enum, audit, and
compatibility semantics in mappers.

Acceptance: context repository tests, schema verification, and no baseline
increase.

## Wave 5 - Remove the exception

Remove the final baseline paths only after all mappings live outside
`acd/domain/`, then replace ADR-028 with a permanent pure-domain rule.

Acceptance: baseline `module_count` is zero, target is zero, the Registry
loads all 92 existing tables, targeted architecture tests pass, and a Full
Quality Gate is green.
