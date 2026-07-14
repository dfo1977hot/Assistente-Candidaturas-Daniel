"""
Architectural conventions for the ACD project.

These tests validate coding conventions adopted by the project.

They intentionally verify only source files under the `acd`
package to avoid false positives from virtual environments,
generated files and third-party code.
"""

from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = PROJECT_ROOT / "acd"

IGNORED_DIRS = {
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    ".pytest_cache",
    ".ruff_cache",
    "build",
    "dist",
    "docs",
    "tools",
}


def python_files() -> list[Path]:
    """Return every Python source file."""

    files: list[Path] = []

    for file in SOURCE_ROOT.rglob("*.py"):
        if any(part in IGNORED_DIRS for part in file.parts):
            continue

        files.append(file)

    return files


# ==========================================================
# File names
# ==========================================================


def test_python_modules_are_snake_case() -> None:
    """Every module should follow snake_case."""

    violations: list[str] = []

    for file in python_files():
        name = file.stem

        if name == "__init__":
            continue

        if name.lower() != name:
            violations.append(str(file.relative_to(PROJECT_ROOT)))
            continue

        if "-" in name:
            violations.append(str(file.relative_to(PROJECT_ROOT)))

    assert not violations, (
        "Invalid module names:\n\n"
        + "\n".join(sorted(violations))
    )


# ==========================================================
# TODO / FIXME
# ==========================================================


def test_source_contains_no_fixme() -> None:
    """FIXME markers should not remain in production code."""

    violations: list[Path] = []

    for file in python_files():
        text = file.read_text(encoding="utf-8")

        if "FIXME" in text:
            violations.append(file.relative_to(PROJECT_ROOT))

    assert violations == []


def test_source_contains_no_todo() -> None:
    """TODO markers should be tracked outside source code."""

    violations: list[Path] = []

    for file in python_files():
        text = file.read_text(encoding="utf-8")

        if "TODO" in text:
            violations.append(file.relative_to(PROJECT_ROOT))

    assert violations == []


# ==========================================================
# print()
# ==========================================================


def test_source_contains_no_print_calls() -> None:
    """Production code should not use print()."""

    violations: list[str] = []

    for file in python_files():
        tree = ast.parse(file.read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "print"
            ):
                violations.append(
                    f"{file.relative_to(PROJECT_ROOT)}:{node.lineno}"
                )

    assert not violations, (
        "print() found:\n\n"
        + "\n".join(violations)
    )


# ==========================================================
# Bare except
# ==========================================================


def test_source_contains_no_bare_except() -> None:
    """Bare except blocks are forbidden."""

    violations: list[str] = []

    for file in python_files():
        tree = ast.parse(file.read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ExceptHandler)
                and node.type is None
            ):
                violations.append(
                    f"{file.relative_to(PROJECT_ROOT)}:{node.lineno}"
                )

    assert not violations


# ==========================================================
# Pass statements
# ==========================================================


def test_source_contains_no_pass_statements() -> None:
    """pass should not remain in production implementations."""

    violations: list[str] = []

    for file in python_files():
        tree = ast.parse(file.read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            if isinstance(node, ast.Pass):
                violations.append(
                    f"{file.relative_to(PROJECT_ROOT)}:{node.lineno}"
                )

    assert not violations


# ==========================================================
# UTF-8 parsing
# ==========================================================


def test_every_python_file_can_be_parsed() -> None:
    """Every module must be valid Python syntax."""

    for file in python_files():
        ast.parse(
            file.read_text(
                encoding="utf-8",
            )
        )