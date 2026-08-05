"""Initial business workflow definitions for the ACD domain."""

from __future__ import annotations

from acd.domain.workflow.workflow_definition import (
    WorkflowCategory,
    WorkflowDefinition,
)
from acd.domain.workflow.workflow_registry import WorkflowRegistry


class WorkflowCatalog:
    """Builds the workflow definitions available in the ACD domain."""

    @staticmethod
    def create_default_registry() -> WorkflowRegistry:
        """Create a registry populated with the initial workflow catalog."""
        registry = WorkflowRegistry()
        for definition in WorkflowCatalog.definitions():
            registry.register(definition)
        return registry

    @staticmethod
    def definitions() -> tuple[WorkflowDefinition, ...]:
        """Return the versioned workflow definitions supported initially."""
        return (
            _workflow(
                "application-v1",
                "Application Workflow",
                "Organiza a candidatura completa para uma nova vaga.",
                WorkflowCategory.APPLICATION,
                (
                    "analyze_job",
                    "select_resume",
                    "gap_analysis",
                    "ats_analysis",
                    "application_strategy",
                    "application_checklist",
                    "persist_application",
                    "complete_application",
                ),
            ),
            _workflow(
                "interview-v1",
                "Interview Workflow",
                "Prepara uma candidatura selecionada para entrevista.",
                WorkflowCategory.INTERVIEW,
                (
                    "select_application",
                    "research_company",
                    "research_interviewer",
                    "prepare_questions",
                    "generate_briefing",
                    "create_study_plan",
                ),
            ),
            _workflow(
                "career-v1",
                "Career Workflow",
                "Estrutura o plano de desenvolvimento profissional.",
                WorkflowCategory.CAREER,
                (
                    "define_professional_goal",
                    "gap_analysis",
                    "assess_competencies",
                    "select_courses",
                    "select_certifications",
                    "create_career_plan",
                    "create_schedule",
                ),
            ),
            _workflow(
                "resume-v1",
                "Resume Workflow",
                "Prepara e revisa um currículo direcionado à vaga.",
                WorkflowCategory.RESUME,
                ("select_resume", "tailor_resume", "review_resume"),
            ),
            _workflow(
                "ats-v1",
                "ATS Workflow",
                "Avalia a compatibilidade entre currículo e vaga.",
                WorkflowCategory.ATS,
                ("select_resume", "analyze_job", "run_ats", "recommend_ats_improvements"),
            ),
        )


def _workflow(
    workflow_id: str,
    name: str,
    description: str,
    category: WorkflowCategory,
    steps: tuple[str, ...],
) -> WorkflowDefinition:
    """Create a versioned workflow definition with linear business dependencies."""
    dependencies = {step: (steps[index - 1],) for index, step in enumerate(steps) if index}
    conditions = {step: f"{dependencies[step][0]}_completed" for step in dependencies}
    return WorkflowDefinition(
        workflow_id=workflow_id,
        name=name,
        description=description,
        version="1.0",
        category=category,
        steps=steps,
        dependencies=dependencies,
        events=("workflow_started", "workflow_completed", "workflow_failed"),
        conditions=conditions,
    )
