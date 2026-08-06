from __future__ import annotations

import pytest

from acd.services.workflow_template_service import (
    WorkflowTemplateService,
)


class DummyWorkflow:
    def __init__(
        self,
        name: str,
        description: str,
        steps: list[dict],
    ):
        self.id = 1
        self.name = name
        self.description = description
        self.steps = steps


class FakeWorkflowService:
    def __init__(self):
        self.calls = []

    def create_workflow(
        self,
        *,
        name,
        description,
        steps,
    ):
        self.calls.append(
            {
                "name": name,
                "description": description,
                "steps": steps,
            }
        )

        return DummyWorkflow(
            name=name,
            description=description,
            steps=steps,
        )


@pytest.fixture
def service():
    workflow_service = FakeWorkflowService()

    service = WorkflowTemplateService(
        workflow_service=workflow_service,
    )

    return service, workflow_service


def test_get_templates(service):
    """Service must return the default templates."""

    template_service, _ = service

    templates = template_service.get_templates()

    assert len(templates) == 4
    assert templates[0]["name"] == "Candidatura Completa"


def test_create_complete_template(service):
    """Complete template must create a workflow."""

    template_service, workflow_service = service

    result = template_service.create_workflow_from_template(
        "Candidatura Completa",
    )

    assert result["name"] == "Candidatura Completa"

    assert len(workflow_service.calls) == 1
    assert (
        workflow_service.calls[0]["description"]
        == "Análise, ATS, geração de documentos e aplicação completa"
    )


def test_template_lookup_is_case_insensitive(service):
    """Template lookup must ignore case."""

    template_service, workflow_service = service

    result = template_service.create_workflow_from_template(
        "apenas ats",
    )

    assert result["name"] == "Apenas ATS"
    assert workflow_service.calls[0]["name"] == "Apenas ATS"


@pytest.mark.parametrize(
    "template_name",
    [
        "Gerar Currículo",
        "Gerar Carta",
    ],
)
def test_create_other_templates(
    service,
    template_name,
):
    """All remaining templates must be creatable."""

    template_service, workflow_service = service

    result = template_service.create_workflow_from_template(
        template_name,
    )

    assert result["name"] == template_name
    assert len(workflow_service.calls) == 1


def test_unknown_template_returns_error(service):
    """Unknown template names must return an error."""

    template_service, workflow_service = service

    result = template_service.create_workflow_from_template(
        "Template Inexistente",
    )

    assert result == {
        "error": "Template not found",
    }

    assert workflow_service.calls == []


def test_all_templates_have_required_fields(service):
    """Every template must expose the expected schema."""

    template_service, _ = service

    templates = template_service.get_templates()

    for template in templates:
        assert "name" in template
        assert "description" in template
        assert "steps" in template
        assert isinstance(template["steps"], list)
        assert len(template["steps"]) > 0


def test_all_steps_have_name_and_command(service):
    """Every workflow step must contain name and command."""

    template_service, _ = service

    templates = template_service.get_templates()

    for template in templates:
        for step in template["steps"]:
            assert "name" in step
            assert "command" in step