"""Tests for generation from an explicit persisted prompt context."""

from __future__ import annotations

from acd.application.prompt.prompt_builder import PromptBuilder, PromptContext
from acd.domain.entities.ai_generation import AIGeneration
from acd.domain.entities.ai_prompt import AIPrompt
from acd.domain.entities.generation_log import GenerationLog
from acd.domain.entities.resume_version import ResumeVersion
from acd.services.ai_generation_service import ResumeGenerationService


class _Repository:
    def __init__(self) -> None:
        self.versions: list[ResumeVersion] = []

    def save_prompt(self, prompt: AIPrompt) -> AIPrompt:
        prompt.id = 1
        return prompt

    def save_generation(self, generation: AIGeneration) -> AIGeneration:
        generation.id = 1
        return generation

    def save_log(self, log: GenerationLog) -> GenerationLog:
        return log

    def save_resume_version(self, version: ResumeVersion) -> ResumeVersion:
        self.versions.append(version)
        return version

    def get_resume_versions(self, curriculum_id: int) -> list[ResumeVersion]:
        return [version for version in self.versions if version.curriculum_id == curriculum_id]


class _Provider:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate_text(self, *, prompt: str, **_: object) -> str:
        self.prompts.append(prompt)
        return "optimized content"


class _ATSServiceThatMustNotRun:
    def compare_curriculum(self, **_: object) -> object:
        raise AssertionError("Persisted-context generation must not run ATS")


def test_generation_from_context_reuses_prompt_and_creates_a_new_version_without_ats() -> None:
    repository = _Repository()
    provider = _Provider()
    service = ResumeGenerationService(
        repository=repository,
        provider=provider,
        prompt_builder=PromptBuilder(),
        ats_service=_ATSServiceThatMustNotRun(),
    )
    context = PromptContext(
        vacancy_title="Backend Engineer",
        vacancy_description="Python and Docker",
        ats_score=80.0,
        missing_skills=None,
        curriculum_summary="Existing curriculum",
        professional_history="Existing curriculum",
    )

    result = service.generate_resume_from_context(curriculum_id=4, context=context)

    assert result["version"] == "v2.0"
    assert provider.prompts == [PromptBuilder().build_resume_prompt(context)]
    assert len(repository.versions) == 1
    assert repository.versions[0].curriculum_id == 4
    assert repository.versions[0].content == "optimized content"
