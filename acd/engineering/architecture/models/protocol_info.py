"""
Protocol model.

Represents a typing.Protocol declaration.
"""

from __future__ import annotations

from dataclasses import dataclass

from acd.engineering.architecture.models.type_info import (
    TypeInfo,
)


@dataclass(slots=True, kw_only=True)
class ProtocolInfo(TypeInfo):
    """
    Represents a Python typing.Protocol declaration.
    """

    runtime_checkable: bool = False

    @property
    def type_kind(self) -> str:
        """
        Returns the type category.
        """

        return "protocol"

    @property
    def is_interface(self) -> bool:
        """
        Protocols behave like interfaces.
        """

        return True

    @property
    def supports_instantiation(self) -> bool:
        """
        Protocols should not be instantiated directly.
        """

        return False

    def __repr__(self) -> str:
        return (
            "ProtocolInfo("
            f"name={self.name!r}, "
            f"runtime_checkable={self.runtime_checkable})"
        )