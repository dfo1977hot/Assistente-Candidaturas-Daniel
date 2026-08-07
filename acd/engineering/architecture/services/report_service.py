"""
Architecture report service.

Generates reports from architecture analysis results.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ReportService:
    """
    Generates reports from architecture analysis.
    """

    def to_dict(
        self,
        analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Returns the analysis dictionary unchanged.

        This method exists to provide a stable API and will
        evolve in future sprints.
        """

        return analysis

    def to_json(
        self,
        analysis: dict[str, Any],
        *,
        indent: int = 4,
    ) -> str:
        """
        Serializes the analysis to JSON.
        """

        return json.dumps(
            analysis,
            indent=indent,
            default=str,
        )

    def save_json(
        self,
        analysis: dict[str, Any],
        output_file: Path,
    ) -> None:
        """
        Saves the analysis as JSON.
        """

        output_file.write_text(
            self.to_json(analysis),
            encoding="utf-8",
        )

    def summary(
        self,
        analysis: dict[str, Any],
    ) -> dict[str, int]:
        """
        Returns a small architecture summary.
        """

        metrics = analysis["metrics"]

        return {
            "modules": metrics.module_count,
            "classes": metrics.class_count,
            "functions": metrics.function_count,
            "dependencies": metrics.dependency_count,
        }