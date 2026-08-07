"""
Project parser.

Coordinates the architectural analysis of a Python project.
"""

from __future__ import annotations

from pathlib import Path

from acd.engineering.architecture.parser.architecture_visitor import (
    ArchitectureVisitor,
)
from acd.engineering.architecture.parser.ast_parser import ASTParser
from acd.engineering.architecture.parser.module_scanner import (
    ModuleScanner,
)


class ProjectParser:
    """
    Coordinates project parsing.

    This class discovers Python files, parses them into ASTs and
    extracts architectural information using the ArchitectureVisitor.
    """

    def __init__(self, root: Path) -> None:
        self._scanner = ModuleScanner(root)
        self._parser = ASTParser()

    @property
    def root(self) -> Path:
        """
        Returns the project root directory.
        """
        return self._scanner.root

    def parse(self) -> list[ArchitectureVisitor]:
        """
        Parses every Python module found in the project.

        Returns
        -------
        list[ArchitectureVisitor]
            One populated visitor per source module.
        """

        visitors: list[ArchitectureVisitor] = []

        for module_path in self._scanner.scan():
            tree = self._parser.parse_file(module_path)

            visitor = ArchitectureVisitor()
            visitor.visit(tree)

            visitors.append(visitor)

        return visitors