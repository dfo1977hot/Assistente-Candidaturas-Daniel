"""Presentation mapping for explicit structured resume generation."""

from __future__ import annotations

from acd.application.structured_resume_version_generation import (
    GenerateStructuredResumeVersionRequest,
    GenerateStructuredResumeVersionUseCase,
)
from acd.presentation.models.structured_resume_generation_view_state import (
    StructuredResumeGenerationViewState,
)


class StructuredResumeGenerationViewModel:
    """Execute the application-safe structured generation use case."""

    _MESSAGES = {
        "success": ("Versão estruturada gerada", "Nova versão estruturada gerada com sucesso. Revise-a antes de adotar."),
        "structured_source_required": ("Currículo sem estrutura", "Este currículo ainda não possui conteúdo estruturado necessário para a geração otimizada."),
        "provider_configuration_required": ("Provider não configurado", "Configure o provider de IA estruturada para gerar uma nova versão."),
        "provider_timeout": ("Tempo esgotado", "Não foi possível concluir a geração no tempo esperado. Tente novamente."),
        "provider_response_invalid": ("Resposta inválida", "O provider retornou uma resposta estruturada inválida."),
        "persistence_failed": ("Falha ao salvar", "A versão foi gerada, mas não pôde ser salva."),
    }

    def __init__(self, use_case: GenerateStructuredResumeVersionUseCase) -> None:
        self._use_case = use_case

    def generate(self, application_id: int) -> StructuredResumeGenerationViewState:
        result = self._use_case.execute(GenerateStructuredResumeVersionRequest(application_id))
        title, message = self._MESSAGES.get(result.status.value, ("Geração não concluída", "Não foi possível gerar a nova versão estruturada."))
        return StructuredResumeGenerationViewState(result.application_id, result.status.value, title, result.message or message, result.status.value == "success", result.resume_version_id, result.version, result.explanation)
