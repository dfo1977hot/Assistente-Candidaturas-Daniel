"""
Dependency graph model.

Represents the dependency graph of the entire project.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass, field

from acd.engineering.architecture.models.dependency import Dependency


@dataclass(slots=True)
class DependencyGraph:
    """
    Aggregate root representing the project dependency graph.
    """

    dependencies: list[Dependency] = field(default_factory=list)

    def add_dependency(self, dependency: Dependency) -> None:
        """
        Adds a dependency if it does not already exist.
        """

        if dependency not in self.dependencies:
            self.dependencies.append(dependency)

    def remove_dependency(self, dependency: Dependency) -> None:
        """
        Removes a dependency.
        """

        if dependency in self.dependencies:
            self.dependencies.remove(dependency)

    def clear(self) -> None:
        """
        Removes every dependency.
        """

        self.dependencies.clear()

    @property
    def dependency_count(self) -> int:
        """
        Returns the number of dependencies.
        """

        return len(self.dependencies)

    @property
    def is_empty(self) -> bool:
        """
        Returns True when no dependencies exist.
        """

        return not self.dependencies

    @property
    def internal_dependencies(self) -> list[Dependency]:
        """
        Returns all internal dependencies.
        """

        return [
            dependency
            for dependency in self.dependencies
            if dependency.is_internal
        ]

    @property
    def external_dependencies(self) -> list[Dependency]:
        """
        Returns all external dependencies.
        """

        return [
            dependency
            for dependency in self.dependencies
            if dependency.is_external
        ]

    def dependencies_from(self, source: str) -> list[Dependency]:
        """
        Returns every dependency originating from a module.
        """

        return [
            dependency
            for dependency in self.dependencies
            if dependency.source == source
        ]

    def dependencies_to(self, target: str) -> list[Dependency]:
        """
        Returns every dependency pointing to a module.
        """

        return [
            dependency
            for dependency in self.dependencies
            if dependency.target == target
        ]

    def successors(self, module: str) -> set[str]:
        """
        Returns every module directly referenced by the given module.
        """

        return {
            dependency.target
            for dependency in self.dependencies
            if dependency.source == module
        }

    def predecessors(self, module: str) -> set[str]:
        """
        Returns every module that references the given module.
        """

        return {
            dependency.source
            for dependency in self.dependencies
            if dependency.target == module
        }

    def adjacency(self) -> dict[str, set[str]]:
        """
        Returns the graph adjacency list.
        """

        graph: dict[str, set[str]] = defaultdict(set)

        for dependency in self.dependencies:
            graph[dependency.source].add(
                dependency.target
            )

        return dict(graph)

    def modules(self) -> set[str]:
        """
        Returns every module in the graph.
        """

        modules: set[str] = set()

        for dependency in self.dependencies:
            modules.add(dependency.source)
            modules.add(dependency.target)

        return modules

    def has_module(self, module: str) -> bool:
        """
        Returns True if the module exists in the graph.
        """

        return module in self.modules()

    def contains(self, source: str, target: str) -> bool:
        """
        Returns True if the dependency exists.
        """

        return any(
            dependency.source == source
            and dependency.target == target
            for dependency in self.dependencies
        )

    def __contains__(self, dependency: Dependency) -> bool:
        return dependency in self.dependencies

    def __len__(self) -> int:
        return self.dependency_count

    def __iter__(self) -> Iterator[Dependency]:
        return iter(self.dependencies)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"dependencies={self.dependency_count})"
        )