"""
Detect circular imports inside the ACD project.

This test builds the import graph of the project and detects cycles
between project modules.

Circular imports are a common source of:

- partially initialized modules
- ImportError
- hidden runtime bugs
- difficult maintenance

The test fails whenever a dependency cycle is detected.
"""

from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ACD_ROOT = PROJECT_ROOT / "acd"


IGNORED_DIRS = {
    "__pycache__",
    ".venv",
    "venv",
    ".git",
    ".pytest_cache",
    ".ruff_cache",
}


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------


def python_files() -> list[Path]:
    files: list[Path] = []

    for file in ACD_ROOT.rglob("*.py"):

        if any(part in IGNORED_DIRS for part in file.parts):
            continue

        files.append(file)

    return files


def module_name(file: Path) -> str:
    relative = file.relative_to(PROJECT_ROOT).with_suffix("")
    return ".".join(relative.parts)


class ImportCollector(ast.NodeVisitor):
    """Collect runtime imports while ignoring TYPE_CHECKING blocks."""

    def __init__(self) -> None:
        self.imports: set[str] = set()
        self._inside_type_checking = False

    def visit_If(self, node: ast.If) -> None:
        previous = self._inside_type_checking
        if isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING":
            self._inside_type_checking = True

        for child in node.body:
            self.visit(child)

        self._inside_type_checking = previous

        for child in node.orelse:
            self.visit(child)

    def visit_Import(self, node: ast.Import) -> None:
        if self._inside_type_checking:
            return
        for alias in node.names:
            if alias.name.startswith("acd."):
                self.imports.add(alias.name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if self._inside_type_checking:
            return
        if node.module and node.module.startswith("acd."):
            self.imports.add(node.module)


def imports_of(file: Path) -> set[str]:
    tree = ast.parse(file.read_text(encoding="utf-8"))
    collector = ImportCollector()
    collector.visit(tree)
    return collector.imports


# ---------------------------------------------------------
# Graph
# ---------------------------------------------------------


def build_graph() -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {}

    modules = {module_name(f) for f in python_files()}

    for file in python_files():

        name = module_name(file)

        deps = set()

        for module in imports_of(file):

            if module in modules:

                deps.add(module)

        graph[name] = deps

    return graph


# ---------------------------------------------------------
# DFS
# ---------------------------------------------------------


def detect_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    visited: set[str] = set()

    stack: list[str] = []

    cycles: list[list[str]] = []

    def visit(node: str) -> None:

        if node in stack:

            start = stack.index(node)

            cycles.append(stack[start:] + [node])

            return

        if node in visited:

            return

        visited.add(node)

        stack.append(node)

        for child in graph.get(node, ()):

            visit(child)

        stack.pop()

    for node in graph:

        visit(node)

    return cycles


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------


def test_project_has_no_circular_imports() -> None:
    graph = build_graph()

    cycles = detect_cycles(graph)

    assert not cycles, (
        "Circular imports detected:\n\n"
        + "\n\n".join(
            " -> ".join(cycle)
            for cycle in cycles
        )
    )


def test_import_graph_is_not_empty() -> None:
    graph = build_graph()

    assert graph


def test_every_module_exists_in_graph() -> None:
    graph = build_graph()

    modules = {module_name(f) for f in python_files()}

    assert modules == set(graph.keys())