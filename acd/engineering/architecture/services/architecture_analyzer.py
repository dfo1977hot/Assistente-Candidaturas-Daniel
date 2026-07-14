"""
Architecture analyzer.

Public façade of the architecture analysis framework.
"""

from __future__ import annotations

from pathlib import Path

from acd.engineering.architecture.parser.project_parser import (
    ProjectParser,
)
from acd.engineering.architecture.services.dependency_graph_service import (
    DependencyGraphService,
)
from acd.engineering.architecture.services.metrics_service import (
    MetricsService,
)


class ArchitectureAnalyzer:
    """
    High-level façade for architecture analysis.

    Coordinates the parsing, dependency graph generation and
    metrics calculation.
    """

    def __init__(self, root: Path) -> None:
        self._parser = ProjectParser(root)
        self._dependency_service = DependencyGraphService()
        self._metrics_service = MetricsService()

    @property
    def root(self) -> Path:
        """
        Returns the analyzed project root.
        """

        return self._parser.root

    def analyze(self) -> dict:
        """
        Executes a complete architecture analysis.

        Returns
        -------
        dict
            Dictionary containing the analysis artifacts.
        """

        visitors = self._parser.parse()

        #
        # Na Sprint 2.1 ainda não convertemos os visitors
        # em ModuleInfo.
        #
        modules = []

        dependency_graph = self._dependency_service.build(modules)

        metrics = self._metrics_service.calculate(
            dependency_graph,
        )

        return {
            "visitors": visitors,
            "modules": modules,
            "dependency_graph": dependency_graph,
            "metrics": metrics,
        }