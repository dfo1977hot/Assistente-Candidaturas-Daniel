from __future__ import annotations

from acd.domain.workflow.workflow_definition import (
    WorkflowCategory,
    WorkflowDefinition,
)
from acd.domain.workflow.workflow_registry import WorkflowRegistry
from acd.domain.workflow.workflow_stage import WorkflowStep
from acd.domain.workflow.workflow_validation import WorkflowValidator


def test_workflow_definition_preserves_business_structure() -> None:
    """A definition exposes the business metadata required by the workflow engine."""
    definition = WorkflowDefinition(
        workflow_id="application-v1",
        name="Candidatura",
        description="Processo de candidatura para uma vaga.",
        version="1.0",
        category=WorkflowCategory.APPLICATION,
        steps=("analyze_job", "select_resume"),
        dependencies={"select_resume": ("analyze_job",)},
        events=("workflow_started", "workflow_completed"),
        conditions={"select_resume": "job_analysis_completed"},
    )

    assert definition.category is WorkflowCategory.APPLICATION
    assert definition.dependencies["select_resume"] == ("analyze_job",)
    assert definition.conditions["select_resume"] == "job_analysis_completed"


def test_workflow_definition_accepts_typed_steps() -> None:
    """Definitions may include business steps with explicit execution metadata."""
    step = WorkflowStep(
        step_id="analyze_job",
        name="Analisar vaga",
        inputs=("job_description",),
        outputs=("job_analysis",),
        timeout_seconds=30,
        rollback_handler="discard_job_analysis",
    )
    definition = WorkflowDefinition(
        workflow_id="application-v1",
        name="Candidatura",
        description="Processo de candidatura para uma vaga.",
        version="1.0",
        category=WorkflowCategory.APPLICATION,
        steps=(step,),
    )

    assert definition.steps == (step,)
    assert step.rollback_handler == "discard_job_analysis"


def test_workflow_registry_registers_and_discovers_definitions() -> None:
    """The registry provides central discovery of workflow definitions."""
    definition = WorkflowDefinition(
        workflow_id="ats-v1",
        name="ATS",
        description="Análise de compatibilidade ATS.",
        version="1.0",
        category=WorkflowCategory.ATS,
        steps=("run_ats",),
    )
    registry = WorkflowRegistry()

    registry.register(definition)

    assert registry.get("ats-v1") is definition
    assert registry.list_all() == (definition,)


def test_workflow_validator_accepts_connected_definition() -> None:
    """A versioned, connected acyclic definition is valid."""
    definition = WorkflowDefinition(
        workflow_id="application-v1",
        name="Candidatura",
        description="Processo de candidatura para uma vaga.",
        version="1.0",
        category=WorkflowCategory.APPLICATION,
        steps=("analyze_job", "select_resume"),
        dependencies={"select_resume": ("analyze_job",)},
    )

    result = WorkflowValidator().validate(definition)

    assert result.is_valid


def test_workflow_validator_reports_graph_and_version_errors() -> None:
    """Invalid identifiers, dependencies, cycles, or versions are reported."""
    definition = WorkflowDefinition(
        workflow_id="application-v1",
        name="Candidatura",
        description="Processo de candidatura para uma vaga.",
        version="",
        category=WorkflowCategory.APPLICATION,
        steps=("analyze_job", "analyze_job", "orphan"),
        dependencies={"analyze_job": ("missing", "analyze_job")},
    )

    result = WorkflowValidator().validate(definition)

    assert not result.is_valid
    assert len(result.errors) == 5
