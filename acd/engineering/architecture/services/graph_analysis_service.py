"""
Graph analysis service.

Provides graph algorithms used by the architecture framework.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping

from acd.engineering.architecture.models.dependency_graph import (
    DependencyGraph,
)


class GraphAnalysisService:
    """
    Graph algorithms over DependencyGraph.

    This service contains reusable graph algorithms that operate
    over DependencyGraph without modifying its state.
    """

    __slots__ = ()

    #
    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    #

    @staticmethod
    def _adjacency(
        graph: DependencyGraph,
    ) -> Mapping[str, set[str]]:
        """
        Returns the graph adjacency list.
        """

        return graph.adjacency()

    def _bfs(
        self,
        graph: DependencyGraph,
        source: str,
    ) -> set[str]:
        """
        Performs a breadth-first search starting at the given module.

        Returns every reachable module, including the source.
        """

        visited: set[str] = set()

        queue: deque[str] = deque([source])

        adjacency = self._adjacency(graph)

        while queue:

            current = queue.popleft()

            if current in visited:
                continue

            visited.add(current)

            for neighbour in adjacency.get(current, ()):

                if neighbour not in visited:
                    queue.append(neighbour)

        return visited

    #
    # ------------------------------------------------------------------
    # Reachability
    # ------------------------------------------------------------------
    #

    def has_path(
        self,
        graph: DependencyGraph,
        source: str,
        target: str,
    ) -> bool:
        """
        Returns True if a path exists between two modules.
        """

        if source == target:
            return True

        return target in self._bfs(graph, source)

    def reachable_nodes(
        self,
        graph: DependencyGraph,
        source: str,
    ) -> set[str]:
        """
        Returns every module reachable from the source module.
        """

        reachable = self._bfs(graph, source)

        reachable.discard(source)

        return reachable

    #
    # ------------------------------------------------------------------
    # Ordering
    # ------------------------------------------------------------------
    #

    def topological_sort(
        self,
        graph: DependencyGraph,
    ) -> list[str]:
        """
        Returns the modules in topological order.

        Raises
        ------
        ValueError
            If the dependency graph contains one or more cycles.
        """

        adjacency = self._adjacency(graph)

        modules = graph.modules()

        in_degree = {
            module: 0
            for module in modules
        }

        for targets in adjacency.values():

            for target in targets:
                in_degree[target] += 1

        queue: deque[str] = deque(
            module
            for module, degree in in_degree.items()
            if degree == 0
        )

        ordered: list[str] = []

        while queue:

            current = queue.popleft()

            ordered.append(current)

            for neighbour in adjacency.get(current, ()):

                in_degree[neighbour] -= 1

                if in_degree[neighbour] == 0:
                    queue.append(neighbour)

        if len(ordered) != len(modules):
            raise ValueError(
                "Dependency graph contains one or more cycles."
            )

        return ordered