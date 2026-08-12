from types import SimpleNamespace

from acd.services.workflow_service import WorkflowService
from acd.services.workflow_template_service import WorkflowTemplateService


class LegacyRepository:
    def __init__(self) -> None:
        self.created = None

    def create_workflow(self, name, description, definition, *, version="1"):
        self.created = SimpleNamespace(
            id=1,
            name=name,
            description=description,
            definition=definition,
            version=version,
        )
        return self.created


def test_create_workflow_accepts_legacy_repository_without_active_attribute() -> None:
    service = WorkflowService(repository=LegacyRepository())
    workflow = service.create_workflow(
        "Meu Workflow",
        "Descrição",
        [{"name": "Passo"}],
    )
    assert workflow.name == "Meu Workflow"


def test_legacy_workflow_templates_remain_available() -> None:
    service = WorkflowTemplateService()
    names = {template["name"] for template in service.get_templates()}
    assert "Candidatura Completa" in names
    assert "Apenas ATS" in names
