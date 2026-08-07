"""
Base model for callable source-code elements.

Represents any executable element discovered in a Python module.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from acd.engineering.architecture.models.source_element import (
    SourceElement,
)


@dataclass(slots=True, kw_only=True)
class CallableInfo(SourceElement):
    """
    Base model for executable Python objects.

    Derived classes:

    - FunctionInfo
    - MethodInfo
    - AsyncFunctionInfo
    - LambdaInfo
    """

    parameters: list[str] = field(default_factory=list)

    return_type: str | None = None

    local_variables: list[str] = field(default_factory=list)

    called_functions: list[str] = field(default_factory=list)

    raised_exceptions: list[str] = field(default_factory=list)

    yields: bool = False

    is_generator: bool = False

    cyclomatic_complexity: int = 1

    lines_of_code: int = 0

    @property
    def parameter_count(self) -> int:
        """
        Returns the number of parameters.
        """
        return len(self.parameters)

    @property
    def local_variable_count(self) -> int:
        """
        Returns the number of local variables.
        """
        return len(self.local_variables)

    @property
    def called_function_count(self) -> int:
        """
        Returns the number of invoked functions.
        """
        return len(self.called_functions)

    @property
    def raised_exception_count(self) -> int:
        """
        Returns the number of explicitly raised exceptions.
        """
        return len(self.raised_exceptions)

    @property
    def has_return_annotation(self) -> bool:
        """
        Indicates whether a return annotation exists.
        """
        return self.return_type is not None

    @property
    def is_complex(self) -> bool:
        """
        Indicates whether the callable exceeds the complexity threshold.
        """
        return self.cyclomatic_complexity >= 10

    @property
    def is_large(self) -> bool:
        """
        Indicates whether the callable is considered large.
        """
        return self.lines_of_code >= 100

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name={self.name!r}, "
            f"parameters={self.parameter_count}, "
            f"complexity={self.cyclomatic_complexity})"
        )