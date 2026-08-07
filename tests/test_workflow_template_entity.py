from __future__ import annotations

from acd.domain.entities.workflow_template import WorkflowTemplate


def test_workflow_template_creation():
    """WorkflowTemplate should initialize correctly."""

    template = WorkflowTemplate(
        name="Template Teste",
    )

    assert template.name == "Template Teste"

    # Defaults do SQLAlchemy somente após persistência.
    assert template.description is None
    assert template.definition is None
    assert template.created_at is None


def test_workflow_template_custom_values():
    """WorkflowTemplate should preserve explicitly supplied values."""

    template = WorkflowTemplate(
        name="Template ATS",
        description="Template para ATS",
        definition='{"steps": [{"command": "run_ats"}]}',
    )

    assert template.name == "Template ATS"
    assert template.description == "Template para ATS"
    assert template.definition == '{"steps": [{"command": "run_ats"}]}'


def test_workflow_template_table_name():
    """WorkflowTemplate should expose the expected table name."""

    assert WorkflowTemplate.__tablename__ == "workflow_templates"


def test_workflow_template_has_primary_key():
    """WorkflowTemplate should expose an id attribute."""

    template = WorkflowTemplate(
        name="Teste",
    )

    assert hasattr(template, "id")


def test_workflow_template_created_at_is_none_before_persist():
    """created_at should not be populated before persistence."""

    template = WorkflowTemplate(
        name="Teste",
    )

    assert template.created_at is None


def test_workflow_template_accepts_empty_definition():
    """WorkflowTemplate should accept an empty definition."""

    template = WorkflowTemplate(
        name="Template",
        definition="",
    )

    assert template.definition == ""


def test_workflow_template_accepts_empty_description():
    """WorkflowTemplate should accept an empty description."""

    template = WorkflowTemplate(
        name="Template",
        description="",
    )

    assert template.description == ""


def test_workflow_template_unique_name_value():
    """The name attribute should preserve the supplied value."""

    template = WorkflowTemplate(
        name="Workflow Completo",
    )

    assert template.name == "Workflow Completo"