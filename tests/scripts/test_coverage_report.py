"""Tests for the isolated coverage-report parser used by the quality gate."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.coverage_report import CoverageReportError, load_coverage_metrics


def _report(
    *,
    global_coverage: float = 69.74,
    branch_coverage: float = 52.29,
) -> dict[str, object]:
    return {
        "meta": {"format": 3},
        "totals": {
            "percent_covered": global_coverage,
            "percent_branches_covered": branch_coverage,
            "covered_lines": 99,
            "num_statements": 100,
            "covered_branches": 52,
            "num_branches": 100,
        },
        "files": {"module.py": {"functions": {"": {}}}},
    }


def _write_report(tmp_path: Path, content: object) -> Path:
    report_path = tmp_path / "coverage.json"
    report_path.write_text(json.dumps(content), encoding="utf-8")
    return report_path


def test_loads_valid_report_with_coverage_and_branch_metrics(tmp_path: Path) -> None:
    """Valid coverage.py totals are exposed without parsing nested file details."""

    metrics = load_coverage_metrics(_write_report(tmp_path, _report()))

    assert metrics.global_coverage == 69.74
    assert metrics.branch_coverage == 52.29
    assert metrics.num_statements == 100
    assert metrics.num_branches == 100


def test_preserves_a_real_zero_percent_coverage(tmp_path: Path) -> None:
    """A valid zero value is distinct from a report parsing failure."""

    metrics = load_coverage_metrics(
        _write_report(tmp_path, _report(global_coverage=0.0, branch_coverage=0.0))
    )

    assert metrics.global_coverage == 0.0
    assert metrics.branch_coverage == 0.0


def test_comparison_with_baseline_uses_real_metric_values(tmp_path: Path) -> None:
    """Both non-regression and regression outcomes use the parsed global coverage."""

    metrics = load_coverage_metrics(_write_report(tmp_path, _report(global_coverage=69.74)))

    assert metrics.global_coverage >= 68.15
    assert metrics.global_coverage < 70.0


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("{invalid", "invalid JSON"),
        ({"meta": {}}, "missing the totals object"),
        ({"totals": {"percent_covered": 50}}, "missing numeric field"),
    ],
)
def test_rejects_invalid_or_incomplete_reports(
    tmp_path: Path, content: object, message: str
) -> None:
    """Malformed structure raises an explicit parser error instead of returning zero."""

    report_path = tmp_path / "coverage.json"
    if isinstance(content, str):
        report_path.write_text(content, encoding="utf-8")
    else:
        report_path.write_text(json.dumps(content), encoding="utf-8")

    with pytest.raises(CoverageReportError, match=message):
        load_coverage_metrics(report_path)


def test_rejects_missing_report(tmp_path: Path) -> None:
    """A missing report is an explicit infrastructure failure."""

    with pytest.raises(CoverageReportError, match="not found"):
        load_coverage_metrics(tmp_path / "missing.json")


def test_cli_returns_explicit_failure_without_emitting_zero(tmp_path: Path) -> None:
    """The PowerShell-facing command reports parser failures through its exit code."""

    report_path = tmp_path / "invalid.json"
    report_path.write_text("{invalid", encoding="utf-8")
    script_path = Path("scripts") / "coverage_report.py"

    completed = subprocess.run(
        [sys.executable, str(script_path), str(report_path)],
        capture_output=True,
        check=False,
        text=True,
    )

    assert completed.returncode == 2
    assert "Coverage report parsing failed" in completed.stderr
    assert "0" not in completed.stdout
