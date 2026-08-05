# Repository Hygiene Inventory

## Estado de entrada

Measured on 2026-08-04 in `refactor/test-infrastructure` at `de57b98`.
There are 75 tracked modifications, 0 staged entries, 580 untracked entries,
and 9,224 ignored entries. No file was deleted, moved, or cleaned by Sprint E.
The coverage baseline is 75.00124075636508% global and 59.732824427480914%
branches. ADR-028 permits the existing 85 domain SQLAlchemy imports only under
the separately validated monotonic-decrease baseline.

## Arquivos rastreados alterados

The tracked changes span productive code, tests, bootstrap, packaging,
configuration, documentation, the local database, and coverage state. They are
accumulated reviewed work, not a cleanup target. `data/database/acd.db`,
`.coverage`, and `coverage.txt` are local state despite current tracking;
future untracking requires a separate reviewed change.

## Arquivos não rastreados e ignorados

| Caminho ou padrão | Quantidade | Estado Git | Categoria | Consumidor | Ação proposta |
|---|---:|---|---|---|---|
| `acd/` | 134 | untracked | código produtivo/recursos | runtime | versionar após revisão; caches permanecem locais |
| `tests/` | 123 | untracked | testes/fixtures | pytest | versionar após revisão |
| `docs/` | 128 | untracked | documentação/governança | mantenedores | versionar após revisão |
| `data/` | 115 | untracked | screenshots/dados locais | automação/usuário | preservar localmente; decisão humana de retenção |
| `scripts/` | 2 | untracked | scripts de diagnóstico | mantenedores | classificar antes de versionar |
| `constraints/` | 1 | untracked | configuração | instalação | candidato a versionamento |
| `quality/` | 1 | untracked | baseline arquitetural | teste ADR-028 | versionar |
| `.sprint-*` | 205 | local | artefatos de Gate | auditoria | preservar e ignorar especificamente |
| `.coverage*`, `coverage.txt` | vários | mixed/local | cobertura | Gate | manter local; somente baselines em `quality/` são versionáveis |
| `.pytest-*`, `.pytest_cache`, `.coverage-runtime` | 9,224 ignored entries | local | cache/basetemp | pytest | ignorar; dívida operacional quando inacessível |
| `build/`, `dist/`, `*.egg-info/` | generated | ignored | build/wheel/sdist | packaging | reproduzir localmente |
| `.venv/`, `venv/` | local | ignored | ambiente virtual | development | nunca versionar |
| `__pycache__/`, `*.py[cod]` | local | ignored | cache | Python | nunca versionar |
| wrappers, PIDs, logs e JSON de Gate na raiz | vários | local | evidência operacional | Gates históricos | preservar e ignorar especificamente |
| `data/database/acd.db` | 1 | modified/local | banco real | desktop | nunca apagar, empacotar ou versionar novamente |

## Diretórios inacessíveis

The inventory observed Permission denied paths below `.pytest-*`,
`.pytest-runtime/`, and generated `acd-*` directories. They are test
basetemps/runtime state, are already covered by targeted ignore rules where
safe, and must not be elevated, inspected forcibly, or removed in this Sprint.
Their existence is operational debt, not evidence that they are empty.

## Artefatos de Quality Gate

There are 205 root `.sprint-*` files totaling 1,372,601 bytes. Sprint C and D
final green evidence, failed attempts, wrappers, stdout/stderr, metadata,
commands, durations, and historical PIDs are cataloged in the preservation
manifest. Raw evidence remains local; no evidence was moved or removed.

## Cobertura e baseline arquitetural ORM

`quality/coverage-baseline.json` remains the sole coverage source of truth.
`quality/domain-sqlalchemy-baseline.json` contains the exact 85 allowed modules,
uses `monotonic-decrease`, and targets zero. Its guard prevents new domain
SQLAlchemy imports; ADR-028 does not authorize ORM migration in Sprint E.

## Bancos, caches, build, scripts e documentação

`DatabaseBootstrap` reconstructs a fresh local schema from the explicit
92-table Registry. Real databases, WAL/SHM, backups, coverage, logs, builds,
and virtual environments remain local. Official scripts are
`run_app.ps1`, `check_project.ps1`, and `quality_gate.ps1`; historical root
wrappers are temporary. Documentation is indexed in place; no bulk move occurs.

## Código legado e arquivos desconhecidos

`domain/agent` and `domain/agents` are separately registered ORM contexts and
are candidates for Sprint F compatibility governance, not deletion. The old
Kernel/Bootstrap paths, containers, experimental wizard/facade, compatibility
imports, and unproven launcher consumers require the same evidence-first
review. A root file named `python.exe -m pytest` and historical wrappers are
operational artifacts, not source.

## Ações propostas

Version reviewed source, tests, documentation, constraints, and baselines.
Keep personal data, databases, credentials, caches, build products, raw Gate
evidence, and temporary wrappers local. Future evidence migration targets
`.local/artifacts/` only after hash verification before and after the move.

## Legacy component matrix

| Componente | Caminho | Consumidores observados | Runtime produtivo | Compatibilidade | Ação futura |
|---|---|---:|---|---|---|
| Agent legacy | `acd/domain/agent/` | 14 referências | Registry ORM | sim | consolidar somente na Sprint F |
| Multi-agent | `acd/domain/agents/` | 13 referências | Registry ORM | sim | governar com o contexto legacy |
| Kernel antigo | `acd/core/kernel/` | 21 referências | parcialmente | investigar | provar caminho de runtime antes de retirar |
| `DependencyContainer` | `acd/` | 17 referências | investigar | sim | inventário de consumidores na Sprint F |
| `ApplicationFacade` | `acd/application/application_facade.py` | 13 referências | experimental | sim | manter isolada até decisão |
| Application wizard | `acd/presentation/pages/application_wizard/` | 10 referências | experimental | sim | manter isolado até decisão |
| `DatabaseBootstrap` | `acd/database/database_bootstrap.py` | 12 referências | sim | n/a | preservar; não é legado removível |
| Root wrappers | raiz `.fast-*`, `.full-*`, `.sprint-*` | histórico | não | n/a | ignorar e preservar como evidência |
| `scripts/quality_gate.py` | removido no worktree acumulado | nenhum script oficial | não | n/a | tratar somente com prova em Sprint F |
