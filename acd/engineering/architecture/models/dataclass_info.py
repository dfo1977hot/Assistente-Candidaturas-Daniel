"""
Dataclass model.

Represents a Python dataclass declaration.
"""

from __future__ import annotations

from dataclasses import dataclass

from acd.engineering.architecture.models.class_info import (
    ClassInfo,
)


@dataclass(slots=True, kw_only=True)
class DataclassInfo(ClassInfo):
    """
    Represents a Python dataclass.
    """

    frozen: bool = False

    order: bool = False

    unsafe_hash: bool = False

    slots_enabled: bool = False

    kw_only: bool = False

    match_args: bool = True

    @property
    def generates_hash(self) -> bool:
        """
        Indicates whether __hash__ is generated.
        """

        return self.frozen or self.unsafe_hash

    @property
    def is_mutable(self) -> bool:
        """
        Indicates whether instances are mutable.
        """

        return not self.frozen

    @property
    def supports_ordering(self) -> bool:
        """
        Indicates whether ordering methods are generated.
        """

        return self.order

    def __repr__(self) -> str:
        return (
            "DataclassInfo("
            f"name={self.name!r}, "
            f"frozen={self.frozen}, "
            f"order={self.order})"
        )