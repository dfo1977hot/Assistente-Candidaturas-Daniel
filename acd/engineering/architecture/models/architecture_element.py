"""
Base model for architectural elements.

Every parsed element in the project derives from this class.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from acd.engineering.architecture.models.source_location import (
    SourceLocation,
)


@dataclass(slots=True, kw_only=True)
class ArchitectureElement:
    """
    Base class for every architectural element.

    Examples
    --------
    - Module
    - Class
    - Function
    - Method
    - Import
    """

    name: str

    location: SourceLocation

    qualified_name_override: str | None = None

    docstring: str | None = None

    decorators: list[str] = field(default_factory=list)

    is_public: bool = True

    @property
    def qualified_name(self) -> str:
        """
        Returns the qualified name of the element.

        Subclasses may override this property to provide
        a more specific qualified name.
        """

        return self.qualified_name_override or self.name

    @property
    def full_name(self) -> str:
        """
        Alias for the qualified name.

        Kept for backward compatibility.
        """

        return self.qualified_name

    @property
    def has_docstring(self) -> bool:
        """
        Returns True if a docstring is available.
        """

        return bool(self.docstring)

    @property
    def has_decorators(self) -> bool:
        """
        Returns True if decorators are present.
        """

        return bool(self.decorators)

    @property
    def is_private(self) -> bool:
        """
        Returns True if the element is private.
        """

        return self.name.startswith("_")

    def __str__(self) -> str:
        return self.qualified_name

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name={self.name!r}, "
            f"qualified_name={self.qualified_name!r})"
        )