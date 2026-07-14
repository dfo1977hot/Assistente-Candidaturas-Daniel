"""
Method model.

Represents a method declared inside a Python class.
"""

from __future__ import annotations

from dataclasses import dataclass

from acd.engineering.architecture.models.callable_info import (
    CallableInfo,
)


@dataclass(slots=True, kw_only=True)
class MethodInfo(CallableInfo):
    """
    Represents a class method.

    Examples
    --------
    class MyClass:

        def execute(...):
            ...

        @staticmethod
        def helper(...):
            ...

        @classmethod
        def create(...):
            ...

        @property
        def name(...):
            ...
    """

    class_name: str = ""

    module_name: str = ""

    is_static: bool = False

    is_class_method: bool = False

    is_property: bool = False

    @property
    def qualified_name(self) -> str:
        """
        Fully-qualified method name.
        """

        parts: list[str] = []

        if self.module_name:
            parts.append(self.module_name)

        if self.class_name:
            parts.append(self.class_name)

        parts.append(self.name)

        return ".".join(parts)

    @property
    def visibility(self) -> str:
        """
        Returns the Python visibility convention.
        """

        if self.name.startswith("__") and not self.name.endswith("__"):
            return "private"

        if self.name.startswith("_"):
            return "protected"

        return "public"

    @property
    def is_magic_method(self) -> bool:
        """
        Returns True if this is a dunder method.
        """

        return (
            self.name.startswith("__")
            and self.name.endswith("__")
        )

    @property
    def is_instance_method(self) -> bool:
        """
        Returns True for regular instance methods.
        """

        return (
            not self.is_static
            and not self.is_class_method
            and not self.is_property
        )

    @property
    def kind(self) -> str:
        """
        Human-readable method type.
        """

        if self.is_property:
            return "property"

        if self.is_class_method:
            return "classmethod"

        if self.is_static:
            return "staticmethod"

        return "instance"

    def __repr__(self) -> str:
        return (
            "MethodInfo("
            f"name={self.name!r}, "
            f"class={self.class_name!r}, "
            f"kind={self.kind!r}, "
            f"complexity={self.cyclomatic_complexity})"
        )