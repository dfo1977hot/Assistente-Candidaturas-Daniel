"""
Module scanner.

Discovers Python source files inside a project directory.
"""

from __future__ import annotations

from pathlib import Path


class ModuleScanner:
    """
    Scans a project for Python modules.
    """

    def __init__(
        self,
        root: Path,
    ) -> None:
        self._root = root

    @property
    def root(self) -> Path:
        """
        Project root directory.
        """

        return self._root

    def scan(self) -> list[Path]:
        """
        Returns every Python module found in the project.
        """

        return sorted(
            path
            for path in self._root.rglob("*.py")
            if self._is_valid_module(path)
        )

    def _is_valid_module(
        self,
        path: Path,
    ) -> bool:
        """
        Filters ignored directories.
        """

        ignored = {
            "__pycache__",
            ".git",
            ".venv",
            "venv",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            ".tox",
            "dist",
            "build",
        }

        return not any(
            part in ignored
            for part in path.parts
        )