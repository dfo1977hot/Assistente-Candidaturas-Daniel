from __future__ import annotations

from acd.domain.entities.workflow import Workflow


def test_workflow_default_values():
    """Workflow should initialize with default values."""

    workflow = Workflow(
        name="Workflow Teste",
        description="Descrição",
        definition='{"steps": []}',
    )

    assert workflow.name == "Workflow Teste"
    assert workflow.description == "Descrição"
    assert workflow.version is None
    assert workflow.definition == '{"steps": []}'
    assert workflow.active is None


def test_workflow_custom_values():
    """Workflow should preserve explicitly supplied values."""

    workflow = Workflow(
        name="Workflow",
        description="Descrição",
        version="2",
        definition='{"steps":[{"name":"A"}]}',
        active=False,
    )

    assert workflow.version == "2"
    assert workflow.active is False
    assert workflow.definition == '{"steps":[{"name":"A"}]}'


def test_workflow_created_at_exists():
    """created_at column should exist."""

    workflow = Workflow(
        name="Workflow",
        description="Descrição",
        definition="{}",
    )

    assert workflow.created_at is None


def test_workflow_updated_at_exists():
    """updated_at column should exist."""

    workflow = Workflow(
        name="Workflow",
        description="Descrição",
        definition="{}",
    )

    assert workflow.updated_at is None


def test_workflow_tablename():
    """Workflow must expose the expected table name."""

    assert Workflow.__tablename__ == "workflows"


def test_workflow_primary_key_exists():
    """Workflow should expose an id attribute."""

    workflow = Workflow(
        name="Workflow",
        description="Descrição",
        definition="{}",
    )

    assert hasattr(workflow, "id")