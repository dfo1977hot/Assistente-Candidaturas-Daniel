"""
Dependency graph service.

Builds a DependencyGraph from parsed modules.
"""

from __future__ import annotations

from acd.engineering.architecture.models.dependency import (
    Dependency,
)
from acd.engineering.architecture.models.dependency_graph import (
    DependencyGraph,
)
from acd.engineering.architecture.models.module_info import (
    ModuleInfo,
)


class DependencyGraphService:
    """
    Creates dependency graphs from parsed modules.
    """

    def build(
        self,
        modules: list[ModuleInfo],
    ) -> DependencyGraph:
        """
        Builds a dependency graph.
        """

        graph = DependencyGraph()

        for module in modules:

            source = module.module_name

            for imported in module.imports:

                graph.add_dependency(
                    Dependency(
                        source=source,
                        target=imported,
                        is_internal=imported.startswith("acd."),
                    )
                )

        return graph