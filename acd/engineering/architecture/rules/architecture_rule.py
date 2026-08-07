"""
Base architecture rule.

Defines the contract implemented by every architecture rule.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class RuleViolation:
    """
    Represents a rule violation.
    """

    rule: str

    message: str

    location: str | None = None


class ArchitectureRule(ABC):
    """
    Base class for every architecture rule.
    """

    @property
    def name(self) -> str:
        """
        Rule name.
        """

        return self.__class__.__name__

    @abstractmethod
    def evaluate(
        self,
        analysis: dict,
    ) -> list[RuleViolation]:
        """
        Evaluates the architecture.

        Returns a list of violations.
        """