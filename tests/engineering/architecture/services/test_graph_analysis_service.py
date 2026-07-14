"""
Tests for GraphAnalysisService.
"""

from __future__ import annotations

import pytest

from acd.engineering.architecture.models.dependency import Dependency
from acd.engineering.architecture.models.dependency_graph import (
    DependencyGraph,
)
from acd.engineering.architecture.services.graph_analysis_service import (
    GraphAnalysisService,
)


@pytest.fixture
def graph() -> DependencyGraph:
    """
    Creates a simple dependency graph.

    A -> B -> C
    A -> D
    """

    graph = DependencyGraph()

    graph.add_dependency(
        Dependency(source="A", target="B")
    )

    graph.add_dependency(
        Dependency(source="B", target="C")
    )

    graph.add_dependency(
        Dependency(source="A", target="D")
    )

    return graph


@pytest.fixture
def service() -> GraphAnalysisService:
    """
    Graph analysis service.
    """

    return GraphAnalysisService()


# ---------------------------------------------------------
# has_path()
# ---------------------------------------------------------


def test_has_path_returns_true(
    service: GraphAnalysisService,
    graph: DependencyGraph,
) -> None:

    assert service.has_path(graph, "A", "C")


def test_has_path_returns_false(
    service: GraphAnalysisService,
    graph: DependencyGraph,
) -> None:

    assert not service.has_path(graph, "C", "A")


def test_has_path_same_module(
    service: GraphAnalysisService,
    graph: DependencyGraph,
) -> None:

    assert service.has_path(graph, "A", "A")


# ---------------------------------------------------------
# reachable_nodes()
# ---------------------------------------------------------


def test_reachable_nodes(
    service: GraphAnalysisService,
    graph: DependencyGraph,
) -> None:

    reachable = service.reachable_nodes(
        graph,
        "A",
    )

    assert reachable == {"B", "C", "D"}


def test_reachable_nodes_leaf(
    service: GraphAnalysisService,
    graph: DependencyGraph,
) -> None:

    reachable = service.reachable_nodes(
        graph,
        "C",
    )

    assert reachable == set()


# ---------------------------------------------------------
# topological_sort()
# ---------------------------------------------------------


def test_topological_sort(
    service: GraphAnalysisService,
    graph: DependencyGraph,
) -> None:

    ordered = service.topological_sort(graph)

    assert ordered.index("A") < ordered.index("B")

    assert ordered.index("B") < ordered.index("C")

    assert ordered.index("A") < ordered.index("D")


def test_topological_sort_cycle() -> None:

    graph = DependencyGraph()

    graph.add_dependency(
        Dependency(source="A", target="B")
    )

    graph.add_dependency(
        Dependency(source="B", target="A")
    )

    service = GraphAnalysisService()

    with pytest.raises(ValueError):

        service.topological_sort(graph)