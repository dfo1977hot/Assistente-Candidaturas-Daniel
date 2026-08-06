# Legacy Retirement Policy

## Productive composition

The productive desktop path is `app.py -> acd.desktop:main ->
DesktopCompositionRoot`. ADR-029 requires explicit constructor wiring and
prohibits Kernel, Bootstrap, legacy container, service-locator, wizard, and
facade composition in that path.

## Retained compatibility and experimental components

| Component | Classification | Official substitute | Removal criterion |
|---|---|---|---|
| `acd.core.kernel` | compatibility | `DesktopCompositionRoot` for runtime composition | prove no test or compatibility consumer remains |
| `register_application_composition` | compatibility/test utility | explicit root wiring | migrate its isolated consumers |
| `acd.domain.agent` | productive bounded context | none; it owns goal/planning tables | schema-neutral migration with consumer, serialization, Registry, and identity evidence |
| `acd.domain.agents` | productive bounded context | canonical namespace for new multi-agent behavior | not a retirement candidate |
| wizard, new-application views, facade | experimental | `ApplicationPage` | approved persistent workflow and no experimental consumer |
| `applicatrion_repository` | legacy compatibility | `infrastructure.repositories.application_repository` | prove contract equivalence and absence of dynamic/external consumers |

## Compatibility rules

Compatibility imports must be explicit, side-effect free, and identity tested.
They cannot create a mapper, metadata, table, registry, or service locator.
`DeprecationWarning` is allowed only for a real compatibility consumer with a
documented substitute and a focused warning test. No warning may occur during
productive ORM model import.

## Mandatory evidence before removal

Removal requires documented searches across source, tests, scripts,
configuration, plugins, serialization, packaging, and documentation; a tested
substitute; green focused validation; unchanged 92-table Registry; and
unchanged or reduced ADR-028 baseline. In doubt, retain, classify, and defer.

## Deferred retirement

The goal/planning and multi-agent contexts cannot be merged by namespace name:
they own distinct ORM models and tables. Full ORM/domain decoupling remains
governed by ADR-028 and is outside Sprint F.
