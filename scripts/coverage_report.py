"""Validate and expose the metrics required by the PowerShell quality gate."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from numbers import Real
from pathlib import Path
import sys
from typing import Any


class CoverageReportError(ValueError):
    """Raised when a coverage JSON report cannot be safely interpreted."""


@dataclass(frozen=True)
class CoverageMetrics:
    """Validated aggregate metrics extracted from a coverage.py JSON report."""

    global_coverage: float
    branch_coverage: float
    covered_lines: int
    num_statements: int
    covered_branches: int
    num_branches: int


def load_coverage_metrics(report_path: Path) -> CoverageMetrics:
    """Load aggregate coverage metrics from a coverage.py JSON report."""

    if not report_path.is_file():
        raise CoverageReportError(f"Coverage report not found: {report_path}")

    try:
        with report_path.open(encoding="utf-8") as report_file:
            report = json.load(report_file)
    except UnicodeDecodeError as error:
        raise CoverageReportError(f"Coverage report is not valid UTF-8: {report_path}") from error
    except json.JSONDecodeError as error:
        raise CoverageReportError(f"Coverage report contains invalid JSON: {report_path}") from error
    except OSError as error:
        raise CoverageReportError(f"Coverage report could not be read: {report_path}") from error

    if not isinstance(report, dict):
        raise CoverageReportError("Coverage report root must be an object.")

    totals = report.get("totals")
    if not isinstance(totals, dict):
        raise CoverageReportError("Coverage report is missing the totals object.")

    return CoverageMetrics(
        global_coverage=_percentage(totals, "percent_covered"),
        branch_coverage=_percentage(totals, "percent_branches_covered"),
        covered_lines=_non_negative_integer(totals, "covered_lines"),
        num_statements=_non_negative_integer(totals, "num_statements"),
        covered_branches=_non_negative_integer(totals, "covered_branches"),
        num_branches=_non_negative_integer(totals, "num_branches"),
    )


def _percentage(totals: dict[str, Any], field: str) -> float:
    value = _number(totals, field)
    if not 0 <= value <= 100:
        raise CoverageReportError(f"Coverage report field '{field}' must be between 0 and 100.")
    return value


def _non_negative_integer(totals: dict[str, Any], field: str) -> int:
    value = _number(totals, field)
    if not value.is_integer() or value < 0:
        raise CoverageReportError(f"Coverage report field '{field}' must be a non-negative integer.")
    return int(value)


def _number(totals: dict[str, Any], field: str) -> float:
    value = totals.get(field)
    if isinstance(value, bool) or not isinstance(value, Real):
        raise CoverageReportError(f"Coverage report is missing numeric field '{field}'.")
    return float(value)


def main(argv: list[str] | None = None) -> int:
    """Print validated metrics as a small JSON object for PowerShell consumers."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report_path", type=Path)
    arguments = parser.parse_args(argv)

    try:
        metrics = load_coverage_metrics(arguments.report_path)
    except CoverageReportError as error:
        print(f"Coverage report parsing failed: {error}", file=sys.stderr)
        return 2

    print(json.dumps(asdict(metrics), separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
