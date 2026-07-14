"""
Module model.

Represents a Python source module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from acd.engineering.architecture.models.container_element import (
    ContainerElement,
)


@dataclass(slots=True, kw_only=True)
class ModuleInfo(ContainerElement):
    """
    Represents a Python module.
    """

    package: str = ""

    relative_path: Path | None = None

    imports: list[str] = field(default_factory=list)

    exported_symbols: list[str] = field(default_factory=list)

    constants: list[str] = field(default_factory=list)

    global_variables: list[str] = field(default_factory=list)

    has_main_block: bool = False

    encoding: str = "utf-8"

    @property
    def module_name(self) -> str:
        """
        Returns the fully-qualified module name.
        """

        if self.package:
            return f"{self.package}.{self.name}"

        return self.name

    @property
    def import_count(self) -> int:
        """
        Returns the number of imports.
        """

        return len(self.imports)

    @property
    def constant_count(self) -> int:
        """
        Returns the number of constants.
        """

        return len(self.constants)

    @property
    def global_count(self) -> int:
        """
        Returns the number of global variables.
        """

        return len(self.global_variables)

    @property
    def export_count(self) -> int:
        """
        Returns the number of exported symbols.
        """

        return len(self.exported_symbols)

    @property
    def is_package_module(self) -> bool:
        """
        Returns True if the module belongs to a package.
        """

        return bool(self.package)

    @property
    def has_exports(self) -> bool:
        """
        Returns True if __all__ exports are defined.
        """

        return self.export_count > 0

    def __repr__(self) -> str:
        return (
            "ModuleInfo("
            f"name={self.module_name!r}, "
            f"imports={self.import_count}, "
            f"classes={self.class_count}, "
            f"functions={self.function_count})"
        )