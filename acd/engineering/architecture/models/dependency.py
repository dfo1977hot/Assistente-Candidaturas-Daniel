"""
Dependency model.

Represents a dependency relationship between two modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from acd.engineering.architecture.models.source_location import (
    SourceLocation,
)


@dataclass(slots=True, frozen=True)
class Dependency:
    """
    Represents a dependency edge in the architecture graph.
    """

    source: str

    target: str

    dependency_type: str = "import"

    is_internal: bool = True

    is_optional: bool = False

    is_dynamic: bool = False

    location: SourceLocation | None = None

    @property
    def is_external(self) -> bool:
        """
        Returns True when the dependency points to an
        external library.
        """

        return not self.is_internal

    @property
    def edge(self) -> tuple[str, str]:
        """
        Returns the graph edge.
        """

        return (
            self.source,
            self.target,
        )

    @property
    def label(self) -> str:
        """
        Human-readable edge label.
        """

        return (
            f"{self.source} -> {self.target}"
        )

    @property
    def has_location(self) -> bool:
        """
        Indicates whether the dependency has a source location.
        """

        return self.location is not None

    @property
    def source_file(self) -> Path | None:
        """
        Returns the file where the dependency was found.
        """

        if self.location is None:
            return None

        return self.location.file

    def __str__(self) -> str:
        return self.label

    def __repr__(self) -> str:
        return (
            "Dependency("
            f"source={self.source!r}, "
            f"target={self.target!r}, "
            f"type={self.dependency_type!r})"
        )