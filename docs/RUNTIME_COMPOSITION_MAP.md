# Runtime Composition Map — Sprint A

`app.py` owns process concerns only: it creates `QApplication`, applies the
theme, asks `DesktopCompositionRoot` for the main window, shows it, and starts
the Qt event loop.

`DesktopCompositionRoot` is the sole productive composition point. It creates
the database schema, repositories, services, presentation pages, sidebar,
router and `MainWindow`. `MainWindow` receives ready-made objects and only
arranges them in a stacked Qt layout.

The fourteen official routes are composed there. The `applications` route maps
only to `ApplicationPage`; `NewApplicationPage` and the wizard are intentionally
not imported or registered by the runtime in Sprint A.

`Kernel`, `Bootstrap`, command bus, query bus and kernel event bus remain for
isolated tests and future migration work only. They are not initialized by
`app.py` or `DesktopCompositionRoot`.

## Validation note

On 2026-08-02 the focused command below rendered 32 passing tests but its
Windows process ended with exit code `-1073740940` (`0xC0000374`):

```powershell
.\.venv\Scripts\python.exe -m pytest tests\presentation\test_application_page_candidate_decision.py -q --maxfail=1
```

Captured stdout ended with `................................ [100%]`; stderr
was empty, and there was no `FAILED`, `ERROR`, `INTERNALERROR`, coverage or
threshold message. A single-test control completed with exit code `0`.
This was classified as a native Qt/PySide process-termination issue after
functional test execution, not a coverage failure or an assertion failure. No
coverage baseline or threshold was changed for Sprint A.

## Sprint status

**Sprint A — Runtime Composition: closed.** The desktop architecture is
validated by the focused composition and UI tests. The ApplicationPage suite
completed all 32 assertions, but it is not classified as green because the
native process did not end successfully.

**Sprint A.1 — Qt Test Process Stability: closed.** The presentation test
fixture now deterministically closes and schedules deletion of every top-level
widget after each test, then flushes deferred Qt deletions through the event
loop. This fixes the ownership/lifetime leak without changing production
behavior or weakening tests.

The focused suite was run three consecutive times in separate processes: each
run reported `32 passed`, exit code `0`, and empty stderr. Coverage governance,
test scope and the desktop runtime were unchanged.

## Sprint A.1 — Qt teardown lifecycle map

`tests/presentation/conftest.py` creates one session-scoped `QApplication` via
`QApplication.instance()` and configures the offscreen platform before that
fixture is used. The ApplicationPage tests create unparented `ApplicationPage`
instances through their local factory. Those pages own all visual children,
including `LongRunningTaskExecutor`; the relevant tests inject synchronous or
deferred `QObject` doubles, so this suite does not start a production
`QThread`. It also creates no timers or dialogs. One test shows a page, making
it a top-level Qt widget until teardown.

Before A.1, the session application outlived all tests but there was no
function-scoped widget teardown: pages and their child C++ objects were left
for Python/Qt shutdown ordering. This was the smallest reproducing condition:
the complete 32-test file completed all assertions and then terminated with
`0xC0000374`; a single test did not.

The `cleanup_qt_widgets` autouse fixture now runs after every Presentation test:

1. obtains all `QApplication.topLevelWidgets()`;
2. closes and calls `deleteLater()` on each;
3. flushes `QEvent.DeferredDelete` events; and
4. processes the event loop before the next test or session shutdown.

Hypothesis results: H1/H12 (multiple or inconsistent QApplication) were ruled
out by the single session fixture and `QApplication.instance()` guard; H3/H9
(unflushed deferred deletion and top-level widgets) was confirmed by the
absence of prior cleanup and the stable result after it; H4/H5/H6 (production
thread, timer or late callback) were ruled out for this suite because its
executors are test doubles and no timers/dialogs are created; H7/H10/H11
(ownership, delayed collection and cross-test interaction) are addressed by
deterministic C++ deletion between tests; H8 (Qt mocks) was not present.

Validation matrix after the correction: full file runs 1, 2 and 3 each
collected and passed 32 tests, exited `0`, and produced empty stderr. The nine
Sprint A composition/UI tests also passed. No Full Gate was run.

## Sprint B — Application flow decision

Sprint B formally classifies `NewApplicationPage`, `application_wizard`,
`NewApplicationViewModel` and `ApplicationFacade` as experimental and outside
the productive desktop runtime. `applications` remains the sole official
route, mapped to `ApplicationPage`; no `applications/new` route exists. The
factual comparison and rationale are recorded in
`docs/architecture/application_flow_decision.md`.
# Database bootstrap governance (Sprint C)

The productive desktop path initializes persistence before repositories:

`app.py -> DesktopCompositionRoot -> engine factory -> DatabaseBootstrap -> load_models() -> SchemaInitializer -> SessionLocal -> repositories/services/pages -> MainWindow`.

`app.py`, `MainWindow`, and Presentation do not create engines or sessions.
The registry loads its 92-table manifest only by explicit `load_models()` call.
For a new database the physical schema must match that manifest; legacy extra
tables (for example `agent_tasks`) are reported and preserved, never removed.

## Local state governance (Sprint G)

The database path is resolved centrally without CWD dependence or import-time
creation. Existing `data/database/acd.db` remains a compatibility path; a fresh
installed application uses the per-user data directory. Explicit bootstrap
creates the parent and validates the 92-table minimum. Backup/restore is a
separate application contract implemented by SQLite infrastructure and is not
an automatic startup or Presentation responsibility.

## Observability and diagnostics governance (Sprint H)

`app.py -> acd.desktop.main -> configure_logging -> DesktopCompositionRoot`
is the only productive logging-composition path. `acd.observability` owns JSON
Lines formatting, context correlation, sanitization, rotation and deterministic
handler teardown. Presentation modules consume logging but do not configure it.

Startup/shutdown, database bootstrap, SQLite backup/restore and long-running
tasks emit bounded technical events. Diagnostics are local, explicit and
read-only with respect to SQLite; support export contains health metadata only,
never database records or absolute filesystem paths. No remote telemetry or
automatic upload participates in the runtime.

## Security and trust-boundary governance (Sprint I)

`acd.security` validates environment-backed secrets, external paths/files,
plugin manifests, optional network endpoints and AI data before Infrastructure
acts. Presentation neither reads secrets nor imports these concrete adapters.
The OpenAI provider receives one allowlisted key, bounded untrusted-data input,
an external HTTPS policy and strict response schema.

Plugins remain outside productive composition, disabled and deny-by-default.
An explicitly invoked loader requires trusted canonical roots and a name
allowlist, does not mutate `sys.path`, and receives no database session, logger
or secret provider. SQLite lifecycle continues to use only explicit validated
paths and never touches the real database during tests.

## Resilience and recovery governance (Sprint J)

`acd.resilience` supplies finite retry, deadline and cooperative-cancellation
contracts to technical boundaries. OpenAI owns explicit transient-error retry
instead of hidden SDK retry; SQLite retries only safe `busy/locked` online-copy
steps. `LongRunningTaskExecutor` remains the sole Qt worker owner and exposes
pending/running/cancelling/cancelled/succeeded/failed/timed_out states.

Backup partials are never promoted, restore validates before atomic replacement,
and plugin failures disable only the optional plugin. Circuit breaker, durable
checkpoints and process-isolated plugins are explicitly deferred.

## Performance and capacity governance (Sprint K)

Startup, composition, bootstrap, initial UI and synthetic Infrastructure
boundaries have official measurements under `tests/performance`. Timings use
tolerant regression ceilings; queue capacity, query count and resource
ownership are hard invariants. `LongRunningTaskExecutor` remains the sole Qt
worker owner with one active slot, no backlog and observable saturation.

No cache, pagination, index, batching or extra concurrency participates in
productive composition without evidence. Tests use isolated databases, fake
OpenAI and synthetic allowlisted plugins; profiles are not package data.
