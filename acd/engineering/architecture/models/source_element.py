"""
Base model for source-code elements.

A SourceElement represents any identifiable element that exists in a
Python source file, such as a module, class, function or method.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from acd.engineering.architecture.models.architecture_element import (
    ArchitectureElement,
)
from acd.engineering.architecture.models.source_location import (
    SourceLocation,
)


@dataclass(slots=True, kw_only=True)
class SourceElement(ArchitectureElement):
    """
    Base class for every source-code element.
    """

    location: SourceLocation

    docstring: str | None = None

    decorators: list[str] = field(default_factory=list)

    annotations: dict[str, str] = field(default_factory=dict)

    is_async: bool = False

    is_public: bool = True

    @property
    def has_annotations(self) -> bool:
        """
        Returns True if type annotations are present.
        """

        return bool(self.annotations)

    @property
    def annotation_count(self) -> int:
        """
        Returns the number of annotations.
        """

        return len(self.annotations)

    @property
    def is_documented(self) -> bool:
        """
        Returns True if the element has a docstring.
        """

        return bool(self.docstring)

    @property
    def decorator_count(self) -> int:
        """
        Returns the number of decorators.
        """

        return len(self.decorators)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name={self.name!r}, "
            f"location={self.location!s})"
        )