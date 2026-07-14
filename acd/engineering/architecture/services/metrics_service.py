"""
Metrics service.

Calculates project architecture metrics from a dependency graph.
"""

from __future__ import annotations

from acd.engineering.architecture.models.dependency_graph import (
    DependencyGraph,
)
from acd.engineering.architecture.models.project_metrics import (
    ProjectMetrics,
)


class MetricsService:
    """
    Calculates architecture metrics.
    """

    def calculate(
        self,
        graph: DependencyGraph,
    ) -> ProjectMetrics:
        """
        Calculates metrics from a dependency graph.
        """

        metrics = ProjectMetrics()

        metrics.dependency_count = graph.dependency_count

        metrics.internal_dependency_count = len(
            graph.internal_dependencies
        )

        metrics.external_dependency_count = len(
            graph.external_dependencies
        )

        return metrics