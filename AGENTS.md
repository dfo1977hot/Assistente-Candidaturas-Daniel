# AGENTS.md — ACD Codex Guide

## Purpose

This repository is the ACD (Assistente de Candidaturas do Daniel), a Windows/Python/PySide6 desktop application.

Before changing code, read `.github/CONSTITUTION.md` and follow it as the primary architecture policy.

## Working branch

Use `develop` as the integration base. Create a task branch when the environment permits it.

Do not commit or open a pull request until all relevant targeted checks pass and the global quality gates pass.

## Required quality gates

Use the project virtual environment:

`C:\Projetos\.venv\Scripts\python.exe`

For every code change:

1. Run targeted `compileall`.
2. Run targeted Ruff with `--fix`.
3. Run targeted Ruff without `--fix`.
4. Run targeted pytest.
5. Before commit, run:
   - `python -m ruff check .`
   - `python -m pytest -q`

A commit is blocked while either global gate fails.

## Architecture rules

- Presentation must not import Infrastructure.
- Presentation must not instantiate Services or Repositories.
- Dependencies are created in the composition root and injected.
- Business rules belong in Services/Domain, never in UI widgets.
- Repositories persist data; they do not implement business rules.
- Prefer small compatible refactors over rewrites.
- Preserve backward compatibility unless a current product rule explicitly supersedes an old behavior.
- Do not add silent `except: pass`, infinite retries, or uncontrolled loops.
- Secret/environment access must remain centralized through approved configuration/secret providers.
- Every Python package under `acd/` must contain `__init__.py`.

## Current product rules that must not regress

### Vagas / Candidaturas remuneration

- `salary_min` is Remuneração oferecida: the real compensation announced by the employer.
- `salary_max` is Remuneração ideal: the market/AI ideal compensation.
- Remuneração oferecida and Remuneração ideal are independent.
- If no offered salary exists, show `A combinar`; persist `None`, never zero.
- In Candidaturas, `Salário esperado` must equal exactly the Vaga `Remuneração ideal`.
- In Candidaturas, `Salário oferecido` is only the employer-announced compensation.
- `Data resposta` starts blank and is filled only when there is an actual response.

### LinkedIn

- Saved-jobs import is incremental.
- Closed jobs must not be imported; existing closed jobs may be removed according to the established confirmation rules.
- Detect and persist the real external application URL when LinkedIn exposes `Candidatar-se`.
- Preserve the full LinkedIn Easy Apply URL, including relevant tracking parameters.
- Do not classify a job as closed merely because an application URL could not be resolved.
- If normalized job URL equals normalized application URL, treat that as closed according to the current business rule.
- Both bulk import and individual link detection must respect the Settings preference for running the LinkedIn browser in the background.

### Gupy

Gupy is manual-only.

- Open the tenant `/candidates/signin` page in the default browser.
- Do not reintroduce automatic passwordless login, question answering, form submission, or unattended application automation.
- Old tests that require Gupy automation are obsolete and should be updated to the manual-only rule rather than restoring removed automation.

### Empresas

- `Buscar dados` should consume API keys saved through Configurações before environment fallbacks.
- `api_key=None` means fallback to configured storage.
- An explicit `api_key=""` means no key, useful for deterministic tests.
- After `Buscar dados` and after `Salvar`, remain on the same company record.

### Cartas

- Letters are linked to jobs/resumes/applications.
- AI generation must not invent experience, achievements, or skills.
- New generations create new versions; never overwrite prior versions.
- Keep a progress bar for AI letter generation in the backlog for a later iteration.

### Workflows

Sprint 1 provides workflow definition, ordered steps, manual execution, progress, history, retry of failed steps, duplication and templates.

The productive workflow engine must reuse existing application services instead of duplicating business logic.

Final submission steps that require user intervention remain `Aguardando usuário`.

## Testing policy

When a global test conflicts with a newer explicit product rule:

1. Confirm the current product rule.
2. Keep the production behavior if it matches the current rule.
3. Update the obsolete test.
4. Do not mutate production behavior only to satisfy a stale assertion.

When a failure reveals an architectural or runtime defect, fix the production code and add/adjust regression tests.

## Current task

Read `docs/codex/global-suite-saneamento.md` before starting the current cleanup task.
