# Legacy component inventory — Sprint F

Consumer searches covered source, tests, scripts, documentation, configuration,
entry points, dynamic-import strings, ORM registry, Composition Root and router.

| Component | Path | Consumers | Productive runtime | Compatibility | Registry/schema | Decision |
|---|---|---|---|---|---|---|
| goal/planning agent domain | `acd/domain/agent` | assistant services and `infrastructure/repositories/agent` | yes, assistant page | no | `agent_goals`, `execution_plans`, `plan_tasks`, `reasoning_steps`, `tool_calls` | retain productive |
| multi-agent domain | `acd/domain/agents` | agent console, multi-agent application/services/repository | yes, agent console | no | `agents`, `agent_*`, `multi_agent_tasks` | retain productive |
| Kernel/Bootstrap/container | `acd/core/kernel` | kernel suites and `infrastructure/query_adapters/registration.py` | no | tested legacy platform | no alternate ORM registry | retain isolated; do not compose |
| wizard/new application | `acd/presentation/pages/application_wizard`, `new_application_*` | experimental tests and view models | no | experimental | none | retain isolated |
| ApplicationFacade | `acd/application/application_facade.py` | experimental view model and tests | no | experimental protocol | none | retain isolated |
| legacy repository spelling | `acd/repositories/applicatrion_repository.py` | legacy compatibility area; no runtime-root import found | no | compatibility is unproven | existing domain repository contract | retain pending consumer and contract analysis |
| Quality Gate Python placeholder | `scripts/quality_gate.py` | absent; removal was already recorded in TD-009 | no | none | none | no file remains to remove |
| kernel package marker | `acd/core/kernel/__init__.py` | Python package boundary | no | package import path | none | retain |

## Namespace decision

`agent` and `agents` are not duplicate namespaces. They model different bounded
contexts and different tables. Both are explicitly present in the 92-table ORM
manifest and both are composed into different productive pages. Aliasing or
removing either namespace would violate the schema-preservation constraint.
Their names remain a discoverability debt; a future rename would require a
schema-neutral import migration and explicit compatibility modules.

For new multi-agent behavior, `acd.domain.agents` is the canonical namespace.
`acd.domain.agent` remains the canonical namespace for the separate goal and
planning context. Neither namespace is an alias of the other.

## Runtime boundary

`app.py -> acd.desktop:main -> DesktopCompositionRoot` contains no Kernel,
Bootstrap, DependencyContainer, wizard or facade construction. Kernel remains a
tested legacy platform, not a productive Composition Root. Experimental
application flows remain importable for tests but have no router/sidebar route.

No `ServiceContainer`, `ServiceLocator`, or `DependencyResolver` was found in
the scanned source, tests, scripts, configuration, or documentation. The
productive health-check registry and connector/field dynamic resolution are
separate runtime features, not composition containers.
