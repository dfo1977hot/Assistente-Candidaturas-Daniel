from __future__ import annotations

import pytest

from acd.services.workflow_template_service import WorkflowTemplateService


class DummyWorkflow:
    def __init__(self, name: str, description: str, steps: list[dict]):
        self.id = 1
        self.name = name
        self.description = description
        self.steps = steps


class FakeWorkflowService:
    def __init__(self):
        self.calls = []

    def create_workflow(self, *, name, description, steps, **kwargs):
        self.calls.append(
            {
                "name": name,
                "description": description,
                "steps": steps,
                **kwargs,
            }
        )
        return DummyWorkflow(name, description, steps)


@pytest.fixture
def service():
    workflow_service = FakeWorkflowService()
    return WorkflowTemplateService(workflow_service=workflow_service), workflow_service


def test_get_templates(service):
    template_service, _ = service
    templates = template_service.get_templates()
    assert len(templates) >= 6
    assert templates[0]["name"] == "Preparação da candidatura"
    assert any(item["name"] == "Candidatura Completa" for item in templates)
    assert any(item["name"] == "Apenas ATS" for item in templates)


def test_preparation_template_contains_manual_checkpoint(service):
    template_service, _ = service
    template = template_service.get_template("Preparação da candidatura")
    assert template is not None
    assert any(step.get("manual") for step in template["steps"])
    assert template["steps"][-1]["command"] == "manual_submit_application"


def test_create_template(service):
    template_service, workflow_service = service
    result = template_service.create_workflow_from_template(
        "Preparação da candidatura"
    )
    assert result["name"] == "Preparação da candidatura"
    assert len(workflow_service.calls) == 1
    assert workflow_service.calls[0]["trigger"] == "Execução manual"


def test_template_lookup_is_case_insensitive(service):
    template_service, _ = service
    assert template_service.get_template("limpeza DE vagas") is not None


def test_unknown_template_returns_error(service):
    template_service, workflow_service = service
    result = template_service.create_workflow_from_template("Template Inexistente")
    assert result == {"error": "Template not found"}
    assert workflow_service.calls == []


def test_all_steps_have_name_and_command(service):
    template_service, _ = service
    for template in template_service.get_templates():
        for step in template["steps"]:
            assert "name" in step
            assert "command" in step
