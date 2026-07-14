"""
Project metrics model.

Represents architecture metrics collected from a project.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, kw_only=True)
class ProjectMetrics:
    """
    Represents high-level architecture metrics.
    """

    module_count: int = 0

    class_count: int = 0

    function_count: int = 0

    method_count: int = 0

    dependency_count: int = 0

    internal_dependency_count: int = 0

    external_dependency_count: int = 0

    circular_dependency_count: int = 0

    abstract_class_count: int = 0

    protocol_count: int = 0

    dataclass_count: int = 0

    enum_count: int = 0

    average_dependencies_per_module: float = 0.0

    average_methods_per_class: float = 0.0

    average_functions_per_module: float = 0.0

    @property
    def total_types(self) -> int:
        """
        Returns the total number of Python types.
        """

        return (
            self.class_count
            + self.protocol_count
            + self.dataclass_count
            + self.enum_count
        )

    @property
    def has_cycles(self) -> bool:
        """
        Indicates whether circular dependencies exist.
        """

        return self.circular_dependency_count > 0

    @property
    def dependency_ratio(self) -> float:
        """
        Average dependencies per module.

        Returns 0.0 if no modules exist.
        """

        if self.module_count == 0:
            return 0.0

        return self.dependency_count / self.module_count

    @property
    def internal_dependency_ratio(self) -> float:
        """
        Percentage of internal dependencies.
        """

        if self.dependency_count == 0:
            return 0.0

        return (
            self.internal_dependency_count
            / self.dependency_count
        )

    @property
    def external_dependency_ratio(self) -> float:
        """
        Percentage of external dependencies.
        """

        if self.dependency_count == 0:
            return 0.0

        return (
            self.external_dependency_count
            / self.dependency_count
        )

    def __repr__(self) -> str:
        return (
            "ProjectMetrics("
            f"modules={self.module_count}, "
            f"classes={self.class_count}, "
            f"dependencies={self.dependency_count})"
        )