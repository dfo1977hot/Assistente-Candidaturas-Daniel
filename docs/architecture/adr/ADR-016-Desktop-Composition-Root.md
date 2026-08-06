# ADR-016 - Desktop Composition Root

## Status

Superseded for composition mechanics by ADR-029

## Contexto

The desktop entry point created `MainWindow` directly. This left no explicit
location to assemble concrete Infrastructure implementations, Application
composition, use cases, and ViewModels.

## Decisao

Adopt `DesktopCompositionRoot` as the desktop assembly point. Its original
container-based mechanics have been replaced by explicit constructor wiring;
ADR-029 is the authoritative decision for the productive runtime.

## Consequencias

Presentation remains independent from Infrastructure and container resolution.
`app.py` remains a thin entry point. The root may know concrete dependencies;
Pages, widgets, ViewModels, and `MainWindow` may not.
