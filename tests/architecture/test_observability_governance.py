"""Architectural guards for observability ownership and privacy."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _files(area: str = "acd") -> list[Path]:
    return list((ROOT / area).rglob("*.py"))


def test_logging_configuration_has_one_owner() -> None:
    offenders = []
    for path in _files():
        source = path.read_text(encoding="utf-8")
        if "basicConfig(" in source or "FileHandler(" in source or "RotatingFileHandler(" in source:
            if path.relative_to(ROOT) != Path("acd/observability/logging_config.py"):
                offenders.append(str(path.relative_to(ROOT)))
    assert not offenders


def test_presentation_does_not_configure_logging_handlers() -> None:
    forbidden = {"FileHandler", "RotatingFileHandler", "TimedRotatingFileHandler", "basicConfig"}
    offenders = []
    for path in _files("acd/presentation"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        names = {node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        names.update(node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name))
        if names & forbidden:
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders


def test_productive_prints_are_confined_to_documented_cli_tools() -> None:
    offenders = []
    for path in _files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print" for node in ast.walk(tree)):
            if path.relative_to(ROOT) != Path("acd/tools/architecture_inventory.py"):
                offenders.append(str(path.relative_to(ROOT)))
    assert not offenders


def test_desktop_entry_point_owns_logging_lifecycle() -> None:
    source = (ROOT / "acd" / "desktop.py").read_text(encoding="utf-8")
    assert "configure_logging()" in source
    assert "close_logging()" in source


def test_local_logs_are_ignored_and_packaging_excludes_them() -> None:
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "*.log" in ignore
    assert '"logs*"' in pyproject
