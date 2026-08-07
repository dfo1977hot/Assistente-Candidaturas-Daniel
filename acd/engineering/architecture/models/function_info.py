"""
Function model.

Represents a module-level Python function.
"""

from __future__ import annotations

from dataclasses import dataclass

from acd.engineering.architecture.models.callable_info import (
    CallableInfo,
)


@dataclass(slots=True, kw_only=True)
class FunctionInfo(CallableInfo):
    """
    Represents a top-level Python function.

    Example
    -------
    def calculate_score(...):
        ...
    """

    module_name: str = ""

    is_nested: bool = False

    @property
    def is_module_function(self) -> bool:
        """
        Returns True when the function belongs directly
        to the module.
        """
        return not self.is_nested

    @property
    def is_nested_function(self) -> bool:
        """
        Returns True if the function is declared
        inside another callable.
        """
        return self.is_nested

    @property
    def qualified_module_name(self) -> str:
        """
        Fully-qualified function name.
        """

        if self.module_name:
            return f"{self.module_name}.{self.name}"

        return self.name

    def __repr__(self) -> str:
        return (
            "FunctionInfo("
            f"name={self.name!r}, "
            f"module={self.module_name!r}, "
            f"parameters={self.parameter_count}, "
            f"complexity={self.cyclomatic_complexity})"
        )