"""
Circular dependency rule.

Detects circular dependencies between project modules.
"""

from __future__ import annotations

from dataclasses import dataclass

from acd.engineering.architecture.models.dependency_graph import (
    DependencyGraph,
)
from acd.engineering.architecture.rules.architecture_rule import (
    ArchitectureRule,
    RuleViolation,
)


@dataclass(slots=True)
class CircularDependencyRule(ArchitectureRule):
    """
    Detects dependency cycles.
    """

    def evaluate(
        self,
        graph: DependencyGraph,
    ) -> list[RuleViolation]:
        """
        Evaluates circular dependencies.

        The actual cycle detection algorithm will be introduced
        in the next sprint.
        """

        #
        # Placeholder implementation.
        #
        # Sprint 2.3:
        # Tarjan Strongly Connected Components
        #

        return []