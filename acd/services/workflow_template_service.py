from __future__ import annotations

from typing import Any

from acd.infrastructure.repositories.workflow_repository import WorkflowRepository
from acd.services.workflow_service import WorkflowService


class WorkflowTemplateService:
    """Provide reusable workflow templates for the desktop designer."""

    DEFAULT_TEMPLATES = [
        {
            "name": "Preparação da candidatura",
            "description": "Prepara vaga, currículo, carta e candidatura até a ação manual.",
            "trigger": "Execução manual",
            "steps": [
                {"name": "Verificar disponibilidade da vaga", "command": "verify_job"},
                {"name": "Detectar URL da candidatura", "command": "detect_application_url"},
                {"name": "Buscar dados da empresa", "command": "enrich_company"},
                {"name": "Pesquisar remuneração", "command": "research_salary"},
                {"name": "Analisar aderência", "command": "analyze_fit"},
                {
                    "name": "Selecionar currículo",
                    "command": "select_resume",
                    "condition": {
                        "field": "fit_score",
                        "operator": ">=",
                        "value": 75,
                        "on_false": "Continuar",
                    },
                },
                {"name": "Gerar currículo otimizado", "command": "generate_resume"},
                {"name": "Gerar carta", "command": "generate_cover_letter"},
                {"name": "Criar/atualizar candidatura", "command": "register_application"},
                {
                    "name": "Concluir candidatura",
                    "command": "manual_submit_application",
                    "manual": True,
                },
            ],
        },
        {
            "name": "Importação e enriquecimento",
            "description": "Valida a vaga e completa os principais dados para decisão.",
            "trigger": "Execução manual",
            "steps": [
                {"name": "Verificar disponibilidade da vaga", "command": "verify_job"},
                {"name": "Detectar URL da candidatura", "command": "detect_application_url"},
                {"name": "Buscar dados da empresa", "command": "enrich_company"},
                {"name": "Pesquisar remuneração", "command": "research_salary"},
            ],
        },
        {
            "name": "Acompanhamento",
            "description": "Organiza o acompanhamento de candidaturas e pontos de atenção.",
            "trigger": "Execução manual",
            "steps": [
                {"name": "Revisar candidatura", "command": "review_application"},
                {"name": "Verificar prazo de follow-up", "command": "check_follow_up"},
                {
                    "name": "Executar follow-up",
                    "command": "manual_follow_up",
                    "manual": True,
                },
            ],
        },
        {
            "name": "Limpeza de vagas",
            "description": "Verifica disponibilidade e prepara a remoção de vagas encerradas.",
            "trigger": "Execução manual",
            "steps": [
                {"name": "Verificar disponibilidade", "command": "verify_job"},
                {"name": "Classificar vaga encerrada", "command": "classify_closed_job"},
            ],
        },
        {
            "name": "Candidatura Completa",
            "description": (
                "Template legado compatível para preparação completa da candidatura."
            ),
            "trigger": "Execução manual",
            "steps": [
                {"name": "Verificar disponibilidade da vaga", "command": "verify_job"},
                {
                    "name": "Detectar URL da candidatura",
                    "command": "detect_application_url",
                },
                {"name": "Buscar dados da empresa", "command": "enrich_company"},
                {"name": "Pesquisar remuneração", "command": "research_salary"},
                {"name": "Analisar aderência", "command": "analyze_fit"},
                {"name": "Selecionar currículo", "command": "select_resume"},
                {"name": "Gerar currículo otimizado", "command": "generate_resume"},
                {"name": "Gerar carta", "command": "generate_cover_letter"},
                {
                    "name": "Criar/atualizar candidatura",
                    "command": "register_application",
                },
                {
                    "name": "Concluir candidatura",
                    "command": "manual_submit_application",
                    "manual": True,
                },
            ],
        },
        {
            "name": "Apenas ATS",
            "description": (
                "Template legado compatível para análise de aderência ATS e currículo."
            ),
            "trigger": "Execução manual",
            "steps": [
                {"name": "Analisar aderência", "command": "analyze_fit"},
                {"name": "Selecionar currículo", "command": "select_resume"},
                {"name": "Gerar currículo otimizado", "command": "generate_resume"},
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
        return [dict(template) for template in self.DEFAULT_TEMPLATES]

    def get_template(self, template_name: str) -> dict[str, Any] | None:
        for template in self.DEFAULT_TEMPLATES:
            if template["name"].casefold() == template_name.casefold():
                return dict(template)
        return None

    def create_workflow_from_template(self, template_name: str) -> dict[str, Any]:
        template = self.get_template(template_name)
        if template is None:
            return {"error": "Template not found"}
        workflow = self.workflow_service.create_workflow(
            name=template["name"],
            description=template["description"],
            steps=template["steps"],
            trigger=template.get("trigger", "Execução manual"),
        )
        return {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
        }
