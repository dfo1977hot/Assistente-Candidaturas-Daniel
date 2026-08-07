# ADR-029 - Containerless Desktop Runtime Composition

## Status

Accepted

## Context

ADR-010, ADR-015, and ADR-016 described a historical container-based
composition path. The productive runtime has since been verified as:

`app.py -> acd.desktop:main -> DesktopCompositionRoot -> DatabaseBootstrap ->
explicit ORM Registry -> MainWindow`.

`DesktopCompositionRoot` constructs the required repositories, services, query
adapters, use cases, view models, pages, router, and window directly. It does
not instantiate `Kernel`, `Bootstrap`, or `DependencyContainer`. The legacy
container and `register_application_composition` remain importable only for
their isolated compatibility and test contracts.

## Decision

1. `DesktopCompositionRoot` is the only productive desktop composition root.
2. Productive composition is explicit and constructor-based; it does not resolve
   dependencies by string, global registry, or legacy container.
3. `Kernel`, `Bootstrap`, `DependencyContainer`, and
   `register_application_composition` are compatibility infrastructure outside
   the productive startup path.
4. ADR-010, ADR-015, and ADR-016 remain historical records, but their
   container-based composition statements are superseded by this ADR.
5. This decision does not remove compatibility components, alter the ORM
   Registry, alter the 92-table schema, or reactivate the experimental wizard
   and facade.

## Consequences

- `app.py`, `acd.desktop`, and Presentation remain free of legacy composition
  infrastructure.
- New productive dependencies must be wired explicitly by
  `DesktopCompositionRoot`.
- Compatibility consumers may continue to use the isolated container until a
  separately approved retirement decision proves removal safe.
- Architecture tests must protect the absence of Kernel, Bootstrap, and
  container construction in the productive runtime.

## Alternatives considered

1. Restore the legacy container to match the older ADR wording. Rejected: it
   would reintroduce global resolution into a tested explicit composition path.
2. Remove the legacy compatibility platform immediately. Rejected: its
   consumers require the evidence-first retirement work planned for Sprint F.
3. Reconcile governance with the verified runtime. Accepted.

## References

- `acd/desktop.py`
- `acd/desktop_composition_root.py`
- `tests/test_desktop_composition_root.py`
- `docs/RUNTIME_COMPOSITION_MAP.md`
