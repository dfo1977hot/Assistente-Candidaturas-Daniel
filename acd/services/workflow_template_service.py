from __future__ import annotations

from typing import Any

from acd.infrastructure.repositories.workflow_repository import WorkflowRepository
from acd.services.workflow_service import WorkflowService


class WorkflowTemplateService:
    """Service for workflow template management."""

    DEFAULT_TEMPLATES = [
        {
            "name": "Candidatura Completa",
            "description": "Análise, ATS, geração de documentos e aplicação completa",
            "steps": [
                {"name": "Análise", "command": "analyze_job"},
                {"name": "ATS", "command": "run_ats"},
                {"name": "Currículo", "command": "generate_resume"},
                {"name": "Carta", "command": "generate_cover_letter"},
                {"name": "Aplicação", "command": "apply_to_job"},
                {"name": "Registro CRM", "command": "register_application"},
            ],
        },
        {
            "name": "Apenas ATS",
            "description": "Análise rápida com scoring ATS",
            "steps": [
                {"name": "Análise", "command": "analyze_job"},
                {"name": "ATS", "command": "run_ats"},
            ],
        },
        {
            "name": "Gerar Currículo",
            "description": "Gera um novo currículo para a vaga",
            "steps": [
                {"name": "Análise", "command": "analyze_job"},
                {"name": "Currículo", "command": "generate_resume"},
            ],
        },
        {
            "name": "Gerar Carta",
            "description": "Gera carta de apresentação para a vaga",
            "steps": [
                {"name": "Análise", "command": "analyze_job"},
                {"name": "Carta", "command": "generate_cover_letter"},
            ],
        },
    ]

    def __init__(
        self,
        workflow_service: WorkflowService | None = None,
        repository: WorkflowRepository | None = None,
    ) -> None:
        self.workflow_service = workflow_service or WorkflowService()
        self.repository = repository or WorkflowRepository()

    def get_templates(self) -> list[dict[str, Any]]:
        """Get list of available templates."""
        return self.DEFAULT_TEMPLATES

    def create_workflow_from_template(self, template_name: str) -> dict[str, Any]:
        """Create a workflow from a template."""
        for template in self.DEFAULT_TEMPLATES:
            if template["name"].lower() == template_name.lower():
                return self.workflow_service.create_workflow(
                    name=template["name"],
                    description=template["description"],
                    steps=template["steps"],
                ).__dict__
        return {"error": "Template not found"}
