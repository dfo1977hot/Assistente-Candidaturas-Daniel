from __future__ import annotations

from typing import Any

import pytest

from acd.application.workflow.execute_domain_workflow import execute_domain_workflow
from acd.domain.workflow.workflow_catalog import WorkflowCatalog
from acd.domain.workflow.workflow_executor import WorkflowExecutor
from acd.domain.workflow.workflow_stage import WorkflowStep


class AnalyzeJobHandler:
    """Test handler for the domain workflow use case."""

    def execute(self, step: WorkflowStep, context: dict[str, Any]) -> None:
        context["job_analysis"] = {"analyzed": True}


def test_execute_domain_workflow_uses_registered_definition() -> None:
    """The use case discovers a definition and delegates execution to the engine."""
    registry = WorkflowCatalog.create_default_registry()
    executor = WorkflowExecutor(handlers={"analyze_job": AnalyzeJobHandler()})

    result = execute_domain_workflow(
        registry,
        executor,
        workflow_id="application-v1",
    )

    assert result.status == "failed"
    assert result.completed_steps == ("analyze_job",)


def test_execute_domain_workflow_rejects_unknown_definition() -> None:
    """The use case reports an identifier absent from the registry."""
    with pytest.raises(LookupError, match="not registered"):
        execute_domain_workflow(
            WorkflowCatalog.create_default_registry(),
            WorkflowExecutor(),
            workflow_id="unknown-v1",
        )
