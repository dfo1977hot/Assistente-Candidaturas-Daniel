"""Focused tests for packaging and application version governance."""

from __future__ import annotations

import importlib.metadata
from pathlib import Path
import tomllib

import acd.core.theme_manager as theme_module
import acd.version as version_module

ROOT = Path(__file__).resolve().parents[1]


def _pyproject() -> dict:
    with (ROOT / "pyproject.toml").open("rb") as stream:
        return tomllib.load(stream)


def test_pyproject_is_the_official_metadata_source() -> None:
    project = _pyproject()["project"]

    assert project["version"] == "0.1.0"
    assert project["requires-python"] == ">=3.14"
    assert {item.split(">=", 1)[0] for item in project["dependencies"]} == {
        "openai", "pandas", "psutil", "pydantic", "PySide6", "python-docx", "SQLAlchemy"
    }
    assert {item.split(">=", 1)[0] for item in project["optional-dependencies"]["dev"]} == {
        "build", "pytest", "pytest-cov", "pytest-qt", "ruff"
    }
    assert project["gui-scripts"]["acd"] == "acd.desktop:main"


def test_requirements_is_utf8_compatibility_delegation() -> None:
    requirements = (ROOT / "requirements.txt").read_bytes()

    assert b"\x00" not in requirements
    assert requirements.decode("utf-8").strip() == "-e ."


def test_version_reads_installed_distribution_metadata(monkeypatch) -> None:
    monkeypatch.setattr(version_module, "version", lambda distribution: "9.8.7")

    assert version_module.get_version() == "9.8.7"


def test_version_has_explicit_uninstalled_source_fallback(monkeypatch) -> None:
    def missing(_distribution: str) -> str:
        raise importlib.metadata.PackageNotFoundError

    monkeypatch.setattr(version_module, "version", missing)

    assert version_module.get_version() == "0+unknown"


def test_wheel_discovery_excludes_workspace_state() -> None:
    setuptools = _pyproject()["tool"]["setuptools"]

    assert setuptools["packages"]["find"]["include"] == ["acd*"]
    assert "data*" in setuptools["packages"]["find"]["exclude"]
    assert setuptools["package-data"]["acd"] == ["resources/styles/*.qss"]


def test_theme_manager_loads_packaged_stylesheet_independently_of_cwd(
    monkeypatch, tmp_path
) -> None:
    stylesheets: list[str] = []
    monkeypatch.chdir(tmp_path)

    class Application:
        def setStyleSheet(self, stylesheet: str) -> None:
            stylesheets.append(stylesheet)

    theme_module.ThemeManager.load(Application())

    assert len(stylesheets) == 1
    assert "QMainWindow" in stylesheets[0]


def test_theme_manager_ignores_missing_packaged_stylesheet(monkeypatch, tmp_path) -> None:
    stylesheets: list[str] = []
    monkeypatch.setattr(theme_module, "files", lambda _package: tmp_path)

    class Application:
        def setStyleSheet(self, stylesheet: str) -> None:
            stylesheets.append(stylesheet)

    theme_module.ThemeManager.load(Application())

    assert stylesheets == []


def test_gitignore_protects_local_state_without_hiding_official_examples() -> None:
    rules = {
        line.strip()
        for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert {
        ".venv/",
        ".pytest_cache/",
        ".coverage",
        ".coverage.*",
        "build/",
        "dist/",
        "*.egg-info/",
        "data/database/*.db",
        "*.db-wal",
        "*.db-shm",
        "*.db-journal",
        "*.sqlite",
        "*.sqlite3",
        "*.journal",
        ".env",
        ".env.*",
        "!.env.example",
        ".local/artifacts/",
        ".sprint-*.stdout.log",
        ".sprint-*.stderr.log",
        ".sprint-*.wrapper.ps1",
        ".sprint-*.gate.pid",
        ".fast-quality-gate-*",
        ".coverage-*.json",
    } <= rules
    assert not {"acd/", "tests/", "docs/", "scripts/", "constraints/"} & rules
    assert "quality/" not in rules


def test_quality_gate_uses_unique_external_basetemp() -> None:
    source = (ROOT / "scripts" / "quality_gate.ps1").read_text(encoding="utf-8")

    assert '[System.IO.Path]::GetTempPath()' in source
    assert '"acd-pytest"' in source
    assert "[guid]::NewGuid()" in source
    assert 'Join-Path $projectRoot ".coverage-runtime"' not in source


def test_packaging_discovery_excludes_local_repository_state() -> None:
    excluded = set(_pyproject()["tool"]["setuptools"]["packages"]["find"]["exclude"])

    assert {"tests*", "data*", "docs*", "logs*", "backups*"} <= excluded
