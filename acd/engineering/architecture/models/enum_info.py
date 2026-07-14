"""
Enumeration model.

Represents a Python enumeration.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from acd.engineering.architecture.models.type_info import (
    TypeInfo,
)


@dataclass(slots=True, kw_only=True)
class EnumInfo(TypeInfo):
    """
    Represents a Python Enum declaration.
    """

    members: list[str] = field(default_factory=list)

    @property
    def type_kind(self) -> str:
        """
        Returns the type category.
        """

        return "enum"

    @property
    def member_count(self) -> int:
        """
        Returns the number of enum members.
        """

        return len(self.members)

    @property
    def is_empty(self) -> bool:
        """
        Indicates whether the enum has members.
        """

        return self.member_count == 0

    def __repr__(self) -> str:
        return (
            "EnumInfo("
            f"name={self.name!r}, "
            f"members={self.member_count})"
        )