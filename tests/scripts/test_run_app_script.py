"""Focused, UI-free checks for the Windows runtime launcher."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest


@pytest.fixture
def launcher() -> Path:
    return Path("scripts/run_app.ps1")


def test_launcher_uses_only_project_relative_virtual_environment(launcher: Path) -> None:
    source = launcher.read_text(encoding="utf-8")

    assert "$PSScriptRoot" in source
    assert ".venv\\Scripts\\python.exe" in source
    assert "$LASTEXITCODE" in source
    assert "& $python -m acd.desktop" in source
    assert "python app.py" not in source


@pytest.mark.parametrize(
    "forbidden",
    ("OPENAI_API_KEY", "OPENAI_MODEL", ".env", "Set-ExecutionPolicy", "openai"),
)
def test_launcher_does_not_manage_dependencies_or_credentials(
    launcher: Path, forbidden: str
) -> None:
    assert forbidden not in launcher.read_text(encoding="utf-8")


def test_launcher_reports_missing_virtual_environment_from_external_directory(
    tmp_path: Path,
    launcher: Path,
) -> None:
    project = tmp_path / "project with spaces"
    scripts = project / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy2(launcher, scripts / launcher.name)
    (project / "app.py").write_text("raise SystemExit(0)", encoding="utf-8")

    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(scripts / launcher.name)],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "Virtual environment" in result.stderr


def test_launcher_reports_missing_desktop_entrypoint_before_invoking_python(
    tmp_path: Path, launcher: Path
) -> None:
    project = tmp_path / "project"
    scripts = project / "scripts"
    python = project / ".venv" / "Scripts" / "python.exe"
    scripts.mkdir(parents=True)
    python.parent.mkdir(parents=True)
    shutil.copy2(launcher, scripts / launcher.name)
    python.write_bytes(b"")

    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(scripts / launcher.name)],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "acd.desktop" in result.stderr
