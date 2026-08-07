# Repository governance

This directory contains versionable summaries governing local state. Raw logs,
coverage databases, PIDs, wheels, databases, screenshots and gate output remain
local and ignored.

- [Worktree inventory](repository_hygiene_inventory.md)
- [Artifact manifest](artifact_preservation_manifest.md)
- [Documentation map](documentation_map.md)
- [Local-files policy](local_files_policy.md)
- [Proposed structure](proposed_repository_structure.md)
- [Future versioning plan](versioning_plan.md)

The inventory does not authorize deletion. ADR-028's [domain persistence
decoupling plan](../architecture/domain_persistence_decoupling_plan.md) governs
the separate ORM migration. Legacy retirement belongs to Sprint F.
