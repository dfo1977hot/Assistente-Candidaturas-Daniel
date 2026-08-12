# Codex Task — Final Global Suite Cleanup

## Goal

Bring the ACD global suite to green without regressing current product rules.

## Baseline observed on 2026-08-11

After the first sanitation pass:

- 1642 tests passed
- 7 tests failed
- 1 test skipped
- no setup errors remained
- global Ruff reported 9 fixable issues

## Remaining failure classes

### 1. Acceptance validation message

`tests/acceptance/test_mvp_validation_messages.py`

Current code returns:

`URL da vaga deve iniciar com http:// ou https://.`

The test expects text beginning with:

`A URL da vaga deve iniciar com http://`

Choose one user-friendly canonical message and align the test with the actual current validation behavior. Do not weaken URL validation.

### 2. Production `pass`

`acd/infrastructure/linkedin/linkedin_saved_jobs_browser.py`

There is a remaining `pass` around line 595 reported by architecture governance.

Replace silent swallowing with explicit safe handling. Preserve LinkedIn import behavior.

### 3. Infinite loop governance

`acd/infrastructure/application_automation/playwright_application_browser.py`

Architecture test detects `while True`.

Refactor to a bounded loop or an equivalent termination-controlled construct. Do not reintroduce Gupy automation.

### 4. Obsolete JobPage resolver test

`tests/presentation/test_job_page_headless_resolver_wiring.py`

The test still expects:

`application_url_resolver: PlaywrightApplicationBrowser | None = None`

Current architecture intentionally decouples Presentation from Infrastructure through the `LinkedInApplicationResolver` boundary.

Update the test to assert the injected protocol/boundary and ensure the composition root injects the Playwright adapter.

Do not restore the Infrastructure import in Presentation.

### 5. Obsolete salary auto-save assertion

`tests/presentation/test_salary_sync_between_jobs_and_applications.py`

The test expects an old call signature:

`self._save_job(clear_form=False)`

The current UI save API uses the newer stay-on-current-record semantics. Align the test with the actual current method/call while preserving automatic persistence after successful salary research.

### 6. Obsolete expected salary formula

The same test still expects:

`expected = (salary_min + salary_max) / 2`

This is obsolete.

Current rule:

`Candidaturas.Salário esperado == Vagas.Remuneração ideal == salary_max`

Update the test. Do not restore averaging or `max(candidates)`.

### 7. Obsolete LinkedIn salary provenance assertion

The same test expects an exact source string that no longer matches implementation.

Verify the current import flow semantically:
- offered employer salary maps to `salary_min`;
- researched ideal salary maps to `salary_max`;
- AI/market research must never overwrite employer-offered salary.

Update the test to the current structure rather than introducing a fake source string.

## Ruff cleanup

Run:

`C:\Projetos\.venv\Scripts\python.exe -m ruff check . --fix`

Then:

`C:\Projetos\.venv\Scripts\python.exe -m ruff check .`

Review every Ruff-generated change before continuing.

## Required validation sequence

First run targeted checks for the touched files/tests.

Then run:

`C:\Projetos\.venv\Scripts\python.exe -m ruff check .`

Finally run:

`C:\Projetos\.venv\Scripts\python.exe -m pytest -q`

The task is complete only if global Ruff and global pytest pass.

Do not commit while either global gate is red.

## Non-goals

- Do not automate Gupy.
- Do not change `Salário esperado` back to max/average logic.
- Do not replace `A combinar` with numeric zero.
- Do not move business rules into Presentation.
- Do not weaken architecture tests to permit Presentation -> Infrastructure coupling.
- Do not delete meaningful governance tests merely to make the suite green.
