"""
Architecture AST visitor.

Traverses a Python AST and collects architectural information.
"""

from __future__ import annotations

import ast


class ArchitectureVisitor(ast.NodeVisitor):
    """
    Base visitor used to extract architectural information
    from Python source code.

    Concrete extraction logic will be added incrementally
    in future sprints.
    """

    def __init__(self) -> None:
        super().__init__()

        self.modules: list[str] = []
        self.classes: list[str] = []
        self.functions: list[str] = []
        self.methods: list[str] = []
        self.imports: list[str] = []

        self._class_depth = 0

    def visit_Module(self, node: ast.Module) -> None:
        """
        Visits the module node.
        """

        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """
        Visits a class declaration.
        """

        self.classes.append(node.name)

        self._class_depth += 1

        self.generic_visit(node)

        self._class_depth -= 1

    def visit_FunctionDef(
        self,
        node: ast.FunctionDef,
    ) -> None:
        """
        Visits a function or method.
        """

        if self._class_depth:

            self.methods.append(node.name)

        else:

            self.functions.append(node.name)

        self.generic_visit(node)

    def visit_AsyncFunctionDef(
        self,
        node: ast.AsyncFunctionDef,
    ) -> None:
        """
        Visits an async function.
        """

        self.visit_FunctionDef(node)

    def visit_Import(
        self,
        node: ast.Import,
    ) -> None:
        """
        Visits import statements.
        """

        for alias in node.names:

            self.imports.append(alias.name)

    def visit_ImportFrom(
        self,
        node: ast.ImportFrom,
    ) -> None:
        """
        Visits from-import statements.
        """

        module = node.module or ""

        for alias in node.names:

            self.imports.append(
                f"{module}.{alias.name}"
            )