# Packaging and version governance

## Decision

`pyproject.toml` is the sole source for package metadata, the supported Python
range, direct runtime dependencies, development tools, the desktop entry point
and application version. The setuptools backend remains in use.

The official application version remains `0.1.0`. It is recorded by the
application release notes and changelog. Tags such as
`v0.9.1-workflow-stable` mark internal architecture milestones and do not form
the package release line; runtime code never derives its version from Git.

`acd.version.get_version()` reads installed distribution metadata. A direct
source-tree import without installed metadata reports `0+unknown` rather than
silently inventing a release. Editable and wheel installations report `0.1.0`.

## Dependency matrix

| PyPI package / import | Productive consumers | Category | Previous origin | Official declaration | Validated version and rationale |
|---|---|---|---|---|---|
| PySide6 / `PySide6` | desktop, UI and Presentation | required runtime | requirements, including separately listed Qt transitives | `PySide6>=6.11.1,<7` | 6.11.1; desktop framework. Addons, Essentials and shiboken remain transitive. |
| SQLAlchemy / `sqlalchemy` | database, ORM models and repositories | required runtime | pyproject range plus requirements pin | `SQLAlchemy>=2.0.51,<3` | 2.0.51; persistence API used throughout the package. `greenlet` remains transitive. |
| OpenAI / `openai` | structured resume provider | required runtime | requirements | `openai>=2.46.0,<3` | 2.46.0; productive provider composed by the desktop root. HTTP clients remain transitive. |
| Pydantic / `pydantic` | structured OpenAI response schema | required runtime | requirements | `pydantic>=2.13.4,<3` | 2.13.4; direct model and validation API. |
| pandas / `pandas` | architecture import analysis | required runtime | requirements | `pandas>=3.0.3,<4` | 3.0.3; direct import in shipped `acd.engineering`. NumPy and date utilities remain transitive. |
| python-docx / `docx` | structured resume DOCX export | required runtime | requirements | `python-docx>=1.2.0,<2` | 1.2.0; productive adapter. lxml remains transitive. |
| psutil / `psutil` | platform metrics and health checks | required runtime | installed but undeclared | `psutil>=7.2.2,<8` | 7.2.2; direct productive and dynamic imports. |
| python-dotenv / `dotenv` | no import or configured plugin found | apparently unused | requirements | not declared | 1.2.2 was present, but environment variables use `os`. |
| openpyxl / `openpyxl` | no productive import found | apparently unused | requirements | not declared | 3.1.5 was present; `et_xmlfile` is its transitive dependency. |
| pytest / `pytest` | test suite | test | environment only | `dev` extra | 9.1.1. |
| pytest-cov / `pytest_cov` | Full Quality Gate coverage options | test | environment only | `dev` extra | 7.1.0. |
| pytest-qt / `pytestqt` | Qt test plugin | test | environment only | `dev` extra | 4.5.0. |
| Ruff / `ruff` | check and quality-gate scripts | development | environment only | `dev` extra | 0.15.22. |
| build / `build` | isolated sdist/wheel validation | build/development | absent | `dev` extra | 1.3.0 target constraint; standards-based setuptools frontend. |
| setuptools, wheel | PEP 517 build environment | build | pyproject build-system | build-system only | setuptools >=80; not application runtime dependencies. |
| typing_extensions, tzdata, six | no direct productive imports | transitive or unused | requirements | not declared | Resolved only when a direct dependency requires them. |

Upper major-version bounds protect the desktop application from unreviewed API
breaks. `constraints/windows-py314.txt` records the direct versions validated on
Windows with CPython 3.14; it is target-specific, not a universal lock and does
not replace package metadata.

## Installation and execution

Runtime installation:

```powershell
python -m pip install -c constraints/windows-py314.txt -e .
acd
```

Development installation:

```powershell
python -m pip install -c constraints/windows-py314.txt -e ".[dev]"
python -m pytest
python -m ruff check .
```

`requirements.txt` is a UTF-8 compatibility shim containing only `-e .`.
It is not an independent dependency list. The installed `acd` GUI entry point
calls `acd.desktop:main`, which composes `DesktopCompositionRoot`. Theme data is
loaded through package resources and does not depend on the current directory.

Package discovery includes only `acd*`; tests, databases, logs, backups,
documentation, Gate artifacts and temporary directories are outside the wheel.
The QSS resource is the sole explicitly packaged data file.

## Python support and quality baseline

The project remains Python `>=3.14` because its Full Gate and packaging
validation have only been performed on CPython 3.14 (currently 3.14.6).
Compatibility below 3.14 has not been proven, so the range is not broadened.
Critical dependencies in the validated environment provide Windows wheels for
this interpreter.

Coverage governance remains separate. `quality/coverage-baseline.json` is the
operational monotonic baseline. Its documentary `test_count` is not updated by
the gate, which promotes only global and branch coverage; therefore 1065 is
preserved rather than manually changed to the latest run's 1302 tests.

## Version inventory

| Location | Previous value/use | Decision |
|---|---|---|
| `pyproject.toml` | `0.1.0`, package metadata | remain as the sole official value |
| `acd/version.py` | duplicated `0.1.0` constant | installed metadata API |
| `acd/config/settings.py` | conflicting `1.0.0` | consume `get_version()` |
| `acd/core/settings.py` | duplicated `0.1.0` | consume `get_version()` |
| `acd/ui/main_window.py` | hard-coded status `v0.1.0` | consume `get_version()` |
| release manager fallback | unrelated hard-coded `0.4.0` | consume `get_version()` |
| feature flag defaults | unrelated hard-coded `0.4.0` | consume `get_version()` |
| release notes/changelog | historical release `0.1.0` | remain as history |
| architecture milestone tags | `v0.8.0`, `v0.9.x-*stable` | remain Git history, never runtime input |
