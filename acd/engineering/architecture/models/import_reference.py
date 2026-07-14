"""
Import reference model.

Represents a single Python import statement extracted from
the Abstract Syntax Tree (AST).
"""

from __future__ import annotations

from dataclasses import dataclass

from acd.engineering.architecture.models.architecture_element import (
    ArchitectureElement,
)


@dataclass(slots=True, kw_only=True)
class ImportReference(ArchitectureElement):
    """
    Represents a Python import statement.

    Examples
    --------
    import os

    import pandas as pd

    from pathlib import Path

    from acd.services.job_service import JobService
    """

    module: str

    imported_name: str | None = None

    alias: str | None = None

    is_relative: bool = False

    level: int = 0

    @property
    def qualified_name(self) -> str:
        """
        Returns the fully-qualified imported symbol.
        """

        if self.imported_name:
            return f"{self.module}.{self.imported_name}"

        return self.module

    @property
    def is_absolute(self) -> bool:
        """
        Returns True if the import is absolute.
        """

        return not self.is_relative

    @property
    def has_alias(self) -> bool:
        """
        Returns True if an alias is defined.
        """

        return self.alias is not None

    @property
    def imported_symbol(self) -> str:
        """
        Returns the imported symbol name.

        Examples
        --------
        JobService

        Path
        """

        return self.imported_name or ""

    @property
    def import_statement(self) -> str:
        """
        Reconstructs the original import statement.
        """

        if self.imported_name:
            statement = (
                f"from {self.module} import {self.imported_name}"
            )
        else:
            statement = f"import {self.module}"

        if self.alias:
            statement += f" as {self.alias}"

        return statement

    def __repr__(self) -> str:
        return (
            "ImportReference("
            f"module={self.module!r}, "
            f"imported_name={self.imported_name!r}, "
            f"alias={self.alias!r})"
        )