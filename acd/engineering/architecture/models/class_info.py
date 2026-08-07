"""
Class model.

Represents a regular Python class.
"""

from __future__ import annotations

from dataclasses import dataclass

from acd.engineering.architecture.models.type_info import (
    TypeInfo,
)


@dataclass(slots=True, kw_only=True)
class ClassInfo(TypeInfo):
    """
    Represents a standard Python class.
    """

    is_final: bool = False

    is_exception: bool = False

    is_inner_class: bool = False

    @property
    def type_kind(self) -> str:
        """
        Returns the type category.
        """

        return "class"

    @property
    def supports_inheritance(self) -> bool:
        """
        Indicates whether inheritance is supported.
        """

        return not self.is_final

    @property
    def is_instantiable(self) -> bool:
        """
        Indicates whether objects of this class can be instantiated.
        """

        return (
            not self.is_abstract
            and not self.is_exception
        )

    def __repr__(self) -> str:
        return (
            "ClassInfo("
            f"name={self.name!r}, "
            f"bases={self.base_count}, "
            f"methods={self.method_count})"
        )