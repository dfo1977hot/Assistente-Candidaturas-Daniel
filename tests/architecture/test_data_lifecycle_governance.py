"""Architectural guards for local data lifecycle governance."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _python_files(directory: str) -> list[Path]:
    return list((ROOT / directory).rglob("*.py"))


def test_presentation_does_not_own_sqlite_or_database_filesystem_operations() -> None:
    forbidden_imports = {"sqlite3", "shutil"}
    offenders: list[str] = []
    for path in _python_files("acd/presentation"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported = {
            node.names[0].name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import) and node.names
        }
        imported.update(
            node.module.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        )
        if imported & forbidden_imports:
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders


def test_productive_code_never_calls_drop_all() -> None:
    offenders = [
        str(path.relative_to(ROOT))
        for path in _python_files("acd")
        if ".drop_all(" in path.read_text(encoding="utf-8")
    ]
    assert not offenders


def test_official_database_path_is_centralized() -> None:
    allowed = {
        Path("acd/database/local_state.py"),
    }
    offenders = []
    for path in _python_files("acd"):
        relative = path.relative_to(ROOT)
        if relative in allowed:
            continue
        source = path.read_text(encoding="utf-8")
        if '"acd.db"' in source or "'acd.db'" in source:
            offenders.append(str(relative))
    assert not offenders


def test_gitignore_excludes_all_sqlite_runtime_companions_and_backups() -> None:
    rules = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert {"*.db-wal", "*.db-shm", "*.db-journal", "*.journal", "*.sqlite", "*.sqlite3"} <= set(rules)
