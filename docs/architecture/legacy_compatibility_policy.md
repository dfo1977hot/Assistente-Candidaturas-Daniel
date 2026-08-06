# Legacy compatibility policy

- A legacy import is retained only with a documented consumer and canonical
  replacement.
- Compatibility modules re-export the canonical object; they do not subclass,
  duplicate ORM mappings, create metadata, or perform registration on import.
- Identity tests are required for aliases.
- Deprecation warnings are added only when a real consumer can migrate without
  polluting official runtime imports.
- Components with distinct tables or behavior are not aliases even when their
  package names are similar.
- Removal requires searches across source, tests, scripts, docs, configuration,
  dynamic imports, serialization names, entry points and Registry ORM.

Current result: no import alias was introduced. `agent` and `agents` are distinct
productive bounded contexts; Kernel and wizard/facade remain isolated contracts.
