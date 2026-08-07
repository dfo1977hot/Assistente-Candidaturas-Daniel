# ADR-028 - Temporary exception for ORM models in the domain namespace

## Status

Accepted - Temporary Architectural Exception

## Context

The current repository is a hybrid ORM/domain architecture. On 2026-08-04,
the Architecture Inventory confirmed that 85 modules below `acd/domain/`
import SQLAlchemy directly. These modules are the productive ORM model set
loaded explicitly by `acd.database.model_registry.ORM_MODEL_MODULES`.

The explicit Registry and `DatabaseBootstrap` preserve the 92-table schema.
Moving or splitting these models during Sprint E would change the repository
hygiene scope into a high-risk persistence migration. Sprint E was therefore
blocked until this pre-existing debt received an explicit, bounded decision.

## Decision

1. The 85 modules listed in `quality/domain-sqlalchemy-baseline.json` are
   accepted temporarily as a hybrid ORM/domain boundary.
2. The baseline is a monotonic-decrease allowlist: existing entries may be
   removed by a future approved migration, but no new domain module may import
   SQLAlchemy.
3. The target remains zero direct SQLAlchemy imports from `acd/domain/`.
4. No second declarative `Base`, implicit model-registration side effect, new
   ORM-coupled domain model, schema/table change, or Registry change is allowed
   under this exception.
5. Migration will be incremental and must preserve table names, relationships,
   serialization behavior, the explicit Registry, and the 92-table manifest.
6. Sprint E is authorized to inventory and document this debt and validate the
   monotonic guard. It must not move entities, modify the Registry, or alter
   the schema.

## Target architecture

The intended boundary separates pure domain entities and value objects from
SQLAlchemy persistence models. Infrastructure owns SQLAlchemy models, mapper
implementations, repositories, and unit-of-work mechanics. Application code
depends on ports; repositories translate persistence models to domain objects.

## Alternatives considered

1. **Migrate all 85 modules now.** Rejected: this is a schema-sensitive,
   cross-cutting refactor outside Sprint E.
2. **Keep ORM in the domain permanently.** Rejected: it preserves framework
   coupling and prevents a pure domain boundary.
3. **Remove the architecture rule.** Rejected: it masks the debt and permits
   growth.
4. **Create a temporary, monotonic exception.** Accepted: it makes the debt
   visible, blocks growth, and enables a safely scoped migration.

## Consequences

Sprint E may resume after this ADR and its guard are validated. The debt
remains explicit and must be retired in a dedicated persistence-boundary
sprint. Compatibility and the current physical schema remain unchanged.

## Exit criteria

- Zero SQLAlchemy imports in `acd/domain/`.
- Pure domain entities and value objects.
- ORM models owned by the persistence layer.
- Tested mappers, repositories, and unit-of-work boundary.
- Explicit Registry updated without changing the 92 tables.
- Non-destructive data/schema validation and a green Full Quality Gate.

## References

- `quality/domain-sqlalchemy-baseline.json`
- `docs/architecture/domain_persistence_decoupling_plan.md`
- `acd/database/model_registry.py`
- `acd/database/database_bootstrap.py`
