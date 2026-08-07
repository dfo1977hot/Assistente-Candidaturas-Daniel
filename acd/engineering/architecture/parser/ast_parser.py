"""
Python AST parser.

Parses Python source files into Abstract Syntax Trees (AST).
"""

from __future__ import annotations

import ast
from pathlib import Path


class ASTParser:
    """
    Parses Python source files.

    This class is intentionally lightweight.
    Higher-level analysis is delegated to dedicated parsers.
    """

    def parse_file(self, path: Path) -> ast.Module:
        """
        Parses a Python source file.

        Parameters
        ----------
        path
            Python source file.

        Returns
        -------
        ast.Module
        """

        source = path.read_text(
            encoding="utf-8",
        )

        return ast.parse(
            source,
            filename=str(path),
            type_comments=True,
        )

    def parse_source(
        self,
        source: str,
        filename: str = "<memory>",
    ) -> ast.Module:
        """
        Parses Python source code from memory.
        """

        return ast.parse(
            source,
            filename=filename,
            type_comments=True,
        )

    @staticmethod
    def walk(tree: ast.AST):
        """
        Iterates over every AST node.
        """

        yield from ast.walk(tree)

    @staticmethod
    def iter_child_nodes(node: ast.AST):
        """
        Iterates over direct child nodes.
        """

        yield from ast.iter_child_nodes(node)

    @staticmethod
    def dump(
        tree: ast.AST,
        *,
        indent: int = 4,
    ) -> str:
        """
        Pretty-prints an AST.
        """

        return ast.dump(
            tree,
            indent=indent,
        )