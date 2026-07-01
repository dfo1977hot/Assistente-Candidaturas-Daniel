from __future__ import annotations

from datetime import datetime
from typing import Any

from acd.application.prompt.prompt_builder import PromptBuilder, PromptContext
from acd.domain.entities.ai_generation import AIGeneration
from acd.domain.entities.ai_prompt import AIPrompt
from acd.domain.entities.cover_letter_version import CoverLetterVersion
from acd.domain.entities.curriculum import Curriculum
from acd.domain.entities.generation_log import GenerationLog
from acd.domain.entities.job_profile import JobProfile
from acd.domain.entities.resume_version import ResumeVersion
from acd.infrastructure.ai.providers import AIProvider, MockAIProvider
from acd.infrastructure.repositories.curriculum_repository import CurriculumRepository
from acd.infrastructure.repositories.prompt_repository import PromptRepository
from acd.services.ats_service import ATSService


class BaseGenerationService:
    """Serviço base para geração assistida por IA."""

    def __init__(
        self,
        repository: PromptRepository | None = None,
        provider: AIProvider | None = None,
        prompt_builder: PromptBuilder | None = None,
        ats_service: ATSService | None = None,
    ) -> None:
        self.repository = repository or PromptRepository()
        self.provider = provider or MockAIProvider()
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.ats_service = ats_service or ATSService()

    def _build_context(self, *, curriculum: Curriculum, job_profile: JobProfile, language: str) -> PromptContext:
        persisted_curriculum = self._ensure_curriculum(curriculum)
        ats_result = self.ats_service.compare_curriculum(curriculum=persisted_curriculum, job_profile=job_profile)
        return PromptContext(
            vacancy_title=job_profile.raw_description[:80],
            vacancy_description=job_profile.raw_description,
            ats_score=float(ats_result.get("total_score", 0.0)),
            missing_skills=list(ats_result.get("gaps", {}).get("missing_skills", [])),
            curriculum_summary=curriculum.description or "",
            professional_history=curriculum.description or "",
            user_goals="Melhorar aderência e visibilidade",
            language=language,
        )

    def _persist_generation(self, *, generation_type: str, prompt: str, response: str, model: str) -> AIGeneration:
        prompt_record = self.repository.save_prompt(
            AIPrompt(template_name=generation_type, version="v1.0", content=prompt)
        )
        generation = self.repository.save_generation(
            AIGeneration(prompt_id=prompt_record.id, generation_type=generation_type, model=model, response_text=response)
        )
        self.repository.save_log(
            GenerationLog(
                generation_id=generation.id,
                model=model,
                response_time_ms=100.0,
                tokens_used=len(response.split()),
                estimated_cost=0.0,
                details="persisted",
            )
        )
        return generation

    def _ensure_curriculum(self, curriculum: Curriculum) -> Curriculum:
        if curriculum.id:
            return curriculum
        return CurriculumRepository().create(curriculum)


class ResumeGenerationService(BaseGenerationService):
    """Gera uma nova versão de currículo com ajuda de IA."""

    def generate_resume(self, *, curriculum: Curriculum, job_profile: JobProfile, language: str) -> dict[str, Any]:
        context = self._build_context(curriculum=curriculum, job_profile=job_profile, language=language)
        prompt = self.prompt_builder.build_resume_prompt(context)
        response = self.provider.generate_text(prompt=prompt, model="mock", temperature=0.2, max_tokens=400, language=language)
        self._persist_generation(generation_type="resume", prompt=prompt, response=response, model="mock")
        version = self.repository.save_resume_version(
            ResumeVersion(
                curriculum_id=curriculum.id,
                version=self._next_version(curriculum.id),
                content=response,
                explanation="Destacadas competências alinhadas à vaga e palavras-chave ATS.",
            )
        )
        return {"content": response, "version": version.version, "explanation": version.explanation}

    def _next_version(self, curriculum_id: int) -> str:
        versions = self.repository.get_resume_versions(curriculum_id)
        if not versions:
            return "v2.0"
        return f"v{len(versions) + 2}.0"


class CoverLetterGenerationService(BaseGenerationService):
    """Gera uma carta de apresentação personalizada."""

    def generate_cover_letter(self, *, curriculum: Curriculum, job_profile: JobProfile, language: str) -> dict[str, Any]:
        context = self._build_context(curriculum=curriculum, job_profile=job_profile, language=language)
        prompt = self.prompt_builder.build_cover_letter_prompt(context)
        response = self.provider.generate_text(prompt=prompt, model="mock", temperature=0.2, max_tokens=400, language=language)
        self._persist_generation(generation_type="cover_letter", prompt=prompt, response=response, model="mock")
        version = self.repository.save_cover_letter_version(
            CoverLetterVersion(
                curriculum_id=curriculum.id,
                version=self._next_version(curriculum.id),
                content=response,
                explanation="Carta adaptada à vaga e ao perfil do candidato.",
            )
        )
        return {"content": response, "version": version.version, "explanation": version.explanation}

    def _next_version(self, curriculum_id: int) -> str:
        versions = self.repository.get_cover_letter_versions(curriculum_id)
        if not versions:
            return "v1.0"
        return f"v{len(versions) + 1}.0"
