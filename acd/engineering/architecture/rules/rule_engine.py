"""
Rule engine.

Executes architecture rules and collects violations.
"""

from __future__ import annotations

from acd.engineering.architecture.rules.architecture_rule import (
    ArchitectureRule,
    RuleViolation,
)


class RuleEngine:
    """
    Executes registered architecture rules.
    """

    def __init__(self) -> None:
        self._rules: list[ArchitectureRule] = []

    @property
    def rules(self) -> tuple[ArchitectureRule, ...]:
        """
        Returns the registered rules.
        """

        return tuple(self._rules)

    def register(
        self,
        rule: ArchitectureRule,
    ) -> None:
        """
        Registers a rule.
        """

        self._rules.append(rule)

    def unregister(
        self,
        rule: ArchitectureRule,
    ) -> None:
        """
        Removes a rule.
        """

        if rule in self._rules:
            self._rules.remove(rule)

    def clear(self) -> None:
        """
        Removes every registered rule.
        """

        self._rules.clear()

    def evaluate(
        self,
        analysis: object,
    ) -> list[RuleViolation]:
        """
        Executes every registered rule.
        """

        violations: list[RuleViolation] = []

        for rule in self._rules:
            violations.extend(
                rule.evaluate(analysis)
            )

        return violations

    @property
    def rule_count(self) -> int:
        """
        Returns the number of registered rules.
        """

        return len(self._rules)

    def __len__(self) -> int:
        return self.rule_count

    def __iter__(self):
        return iter(self._rules)

    def __repr__(self) -> str:
        return (
            f"RuleEngine("
            f"rules={self.rule_count})"
        )