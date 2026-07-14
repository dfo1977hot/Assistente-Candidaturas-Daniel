"""
Base model for source-code containers.

A ContainerElement represents any source-code element capable of
containing other architectural elements, such as modules or classes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from acd.engineering.architecture.models.import_reference import (
    ImportReference,
)
from acd.engineering.architecture.models.source_element import (
    SourceElement,
)


@dataclass(slots=True, kw_only=True)
class ContainerElement(SourceElement):
    """
    Base class for elements that contain other elements.
    """

    imports: list[ImportReference] = field(default_factory=list)

    functions: list[str] = field(default_factory=list)

    classes: list[str] = field(default_factory=list)

    submodules: list[str] = field(default_factory=list)

    @property
    def import_count(self) -> int:
        """Returns the number of imports."""

        return len(self.imports)

    @property
    def function_count(self) -> int:
        """Returns the number of functions."""

        return len(self.functions)

    @property
    def class_count(self) -> int:
        """Returns the number of classes."""

        return len(self.classes)

    @property
    def submodule_count(self) -> int:
        """Returns the number of submodules."""

        return len(self.submodules)

    @property
    def is_empty(self) -> bool:
        """Returns True if the container has no children."""

        return (
            self.import_count == 0
            and self.function_count == 0
            and self.class_count == 0
            and self.submodule_count == 0
        )

    @property
    def child_count(self) -> int:
        """Returns the total number of child elements."""

        return (
            self.import_count
            + self.function_count
            + self.class_count
            + self.submodule_count
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name={self.name!r}, "
            f"children={self.child_count})"
        )