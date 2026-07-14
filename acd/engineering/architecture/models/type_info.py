"""
Base model for Python types.

Represents any Python type declaration such as classes,
enums, protocols and dataclasses.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from acd.engineering.architecture.models.container_element import (
    ContainerElement,
)


@dataclass(slots=True, kw_only=True)
class TypeInfo(ContainerElement):
    """
    Base class for Python type declarations.
    """

    bases: list[str] = field(default_factory=list)

    attributes: list[str] = field(default_factory=list)

    methods: list[str] = field(default_factory=list)

    nested_types: list[str] = field(default_factory=list)

    is_abstract: bool = False

    is_generic: bool = False

    @property
    def base_count(self) -> int:
        """Returns the number of base classes."""

        return len(self.bases)

    @property
    def attribute_count(self) -> int:
        """Returns the number of attributes."""

        return len(self.attributes)

    @property
    def method_count(self) -> int:
        """Returns the number of methods."""

        return len(self.methods)

    @property
    def nested_type_count(self) -> int:
        """Returns the number of nested types."""

        return len(self.nested_types)

    @property
    def member_count(self) -> int:
        """Returns the total number of members."""

        return (
            self.attribute_count
            + self.method_count
            + self.nested_type_count
        )

    @property
    def has_base_classes(self) -> bool:
        """Returns True if inheritance exists."""

        return self.base_count > 0

    @property
    def is_leaf_type(self) -> bool:
        """Returns True if the type contains no nested types."""

        return self.nested_type_count == 0

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name={self.name!r}, "
            f"bases={self.base_count}, "
            f"members={self.member_count})"
        )