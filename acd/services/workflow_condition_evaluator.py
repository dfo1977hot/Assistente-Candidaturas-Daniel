from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ConditionResult:
    matched: bool
    field: str
    operator: str
    expected: Any
    observed: Any


class WorkflowConditionEvaluator:
    """Evaluate a small allow-listed condition language without dynamic code."""

    FIELDS = frozenset(
        {
            "job_id",
            "application_id",
            "curriculum_id",
            "fit_score",
            "salary_ideal",
            "salary_offered",
            "application_url",
            "company_id",
            "application_status",
        }
    )
    OPERATORS = (
        "==",
        "!=",
        ">",
        ">=",
        "<",
        "<=",
        "contém",
        "não contém",
        "está vazio",
        "não está vazio",
    )

    def evaluate(self, condition: dict[str, Any], context: dict[str, Any]) -> ConditionResult:
        field = str(condition.get("field") or "")
        operator = str(condition.get("operator") or "")
        expected = condition.get("value")
        if field not in self.FIELDS:
            raise ValueError(f"Campo de condição não permitido: {field}")
        if operator not in self.OPERATORS:
            raise ValueError(f"Operador de condição não permitido: {operator}")
        observed = context.get(field)
        matched = self._compare(operator, observed, expected)
        return ConditionResult(matched, field, operator, expected, observed)

    @classmethod
    def _compare(cls, operator: str, observed: Any, expected: Any) -> bool:
        if operator == "está vazio":
            return cls._empty(observed)
        if operator == "não está vazio":
            return not cls._empty(observed)
        if operator == "contém":
            return str(expected).casefold() in str(observed or "").casefold()
        if operator == "não contém":
            return str(expected).casefold() not in str(observed or "").casefold()
        left, right = cls._coerce_pair(observed, expected)
        comparisons = {
            "==": lambda: left == right,
            "!=": lambda: left != right,
            ">": lambda: left > right,
            ">=": lambda: left >= right,
            "<": lambda: left < right,
            "<=": lambda: left <= right,
        }
        try:
            return bool(comparisons[operator]())
        except TypeError:
            return False

    @staticmethod
    def _empty(value: Any) -> bool:
        return value is None or value == "" or value == () or value == [] or value == {}

    @staticmethod
    def _coerce_pair(left: Any, right: Any) -> tuple[Any, Any]:
        if isinstance(left, bool):
            return left, str(right).casefold() in {"true", "1", "sim"}
        if isinstance(left, (int, float)):
            try:
                return float(left), float(right)
            except (TypeError, ValueError):
                return left, right
        return left, right
