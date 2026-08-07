"""
Layer architecture rule.

Checks forbidden dependencies between architectural layers.
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
class LayerRule(ArchitectureRule):
    """
    Validates architectural layer dependencies.
    """

    forbidden: dict[str, set[str]]

    def evaluate(
        self,
        graph: DependencyGraph,
    ) -> list[RuleViolation]:
        """
        Evaluates forbidden layer dependencies.
        """

        violations: list[RuleViolation] = []

        for dependency in graph:

            source_layer = self._layer(dependency.source)
            target_layer = self._layer(dependency.target)

            forbidden_targets = self.forbidden.get(
                source_layer,
                set(),
            )

            if target_layer in forbidden_targets:

                violations.append(
                    RuleViolation(
                        rule=self.name,
                        message=(
                            f"{source_layer} cannot depend on "
                            f"{target_layer}"
                        ),
                        location=dependency.label,
                    )
                )

        return violations

    @staticmethod
    def _layer(
        module_name: str,
    ) -> str:
        """
        Returns the first package segment.

        Example
        -------
        acd.services.jobs -> services
        """

        parts = module_name.split(".")

        if len(parts) >= 2:
            return parts[1]

        return module_name