# Future Versioning Plan

No commit is executed by Sprint E. Each future commit must isolate reviewed
changes, exclude local evidence, and run its focused tests.

| Order | Group | Dependencies/tests | Risk | Suggested message |
|---:|---|---|---|---|
| 1 | Composition Root and runtime | desktop/root tests | startup | `refactor(runtime): compose desktop startup` |
| 2 | Qt teardown | presentation teardown tests | resource lifecycle | `test(ui): cover Qt teardown` |
| 3 | Application workflow | application/repository tests | behavior | `feat(application): stabilize candidate workflow` |
| 4 | Registry and DatabaseBootstrap | Registry/92-table tests | schema compatibility | `refactor(database): make bootstrap deterministic` |
| 5 | Packaging and version | packaging/wheel tests | distribution | `build(package): govern package metadata` |
| 6 | Quality Gate and basetemp | Gate wrapper tests | test isolation | `test(quality): isolate gate basetemp` |
| 7 | ADR-028 and ORM baseline | monotonic guard | architectural debt | `docs(architecture): govern domain ORM exception` |
| 8 | Tests and coverage | coverage policy tests | baseline monotonicity | `test(coverage): recover governed baseline` |
| 9 | Documentation | link and focused docs review | stale references | `docs: synchronize architecture governance` |
| 10 | Repository hygiene | ignore/governance tests | accidental omission | `chore(repository): govern local artifacts` |
| 11 | Legacy retirement | Sprint F evidence/tests | compatibility | `refactor(legacy): retire proven compatibility paths` |
| 12 | Domain/persistence decoupling | ADR-028 exit criteria | schema and serialization | `refactor(persistence): extract ORM mappings` |
