"""Tests for structured resume generation before Presentation integration."""

from __future__ import annotations

from types import SimpleNamespace

from acd.application.query_ports import VacancyQueryDTO
from acd.application.resume_optimization.resume_optimization_workflow import (
    ResumeOptimizationAvailability,
)
from acd.application.structured_resume_generation import (
    StructuredGenerationCapabilities,
    StructuredResumeProviderResult,
    StructuredResumeProviderStatus,
)
from acd.application.structured_resume_snapshot import StructuredResumeSnapshotCodec
from acd.application.structured_resume_version_generation import (
    CreatedStructuredResumeVersion,
    GenerateStructuredResumeVersionRequest,
    GenerateStructuredResumeVersionUseCase,
    StructuredResumeTextRenderer,
)


def _snapshot():
    return StructuredResumeSnapshotCodec().from_payload(
        {
            "schema_version": 1,
            "identity": {"full_name": "Dаниel", "professional_title": "Engineer", "location": "São Paulo"},
            "contact": {"email": "daniel@example.com", "phone": None, "linkedin": None, "portfolio": None, "website": None},
            "summary": "Python specialist", "skills": ["Python"], "experiences": [],
            "education": [], "certifications": [], "courses": [], "languages": [],
            "projects": [], "additional_sections": [],
        }
    )


class FakeWorkflow:
    def execute(self, application_id: int) -> object:
        return SimpleNamespace(
            availability=ResumeOptimizationAvailability.READY,
            application_id=application_id,
            curriculum_id=10,
            resume=SimpleNamespace(structured_resume=_snapshot()),
            vacancy=VacancyQueryDTO(2, "Engineer", 3, "Python"),
        )


class FakeProvider:
    def get_capabilities(self) -> StructuredGenerationCapabilities:
        return StructuredGenerationCapabilities(True, True, (1,), "fake")

    def generate_structured_resume(self, request: object) -> StructuredResumeProviderResult:
        del request
        return StructuredResumeProviderResult(
            StructuredResumeProviderStatus.SUCCESS, _snapshot(), "Explanation"
        )


class FakeWritePort:
    def __init__(self) -> None:
        self.requests: list[object] = []

    def create_structured_resume_version(self, request: object) -> CreatedStructuredResumeVersion:
        self.requests.append(request)
        return CreatedStructuredResumeVersion(99, "v2.0")


def test_renderer_is_deterministic_preserves_unicode_and_omits_empty_sections() -> None:
    renderer = StructuredResumeTextRenderer()

    first = renderer.render(_snapshot())

    assert first == renderer.render(_snapshot())
    assert "Dаниel" in first
    assert "CERTIFICAÇÕES" not in first


def test_use_case_derives_text_and_json_from_provider_snapshot_without_adoption() -> None:
    write_port = FakeWritePort()
    use_case = GenerateStructuredResumeVersionUseCase(
        FakeWorkflow(), FakeProvider(), StructuredResumeTextRenderer(), write_port
    )

    result = use_case.execute(GenerateStructuredResumeVersionRequest(1))

    assert result.status.value == "success"
    assert (result.resume_version_id, result.version) == (99, "v2.0")
    saved = write_port.requests[0]
    assert "Dаниel" in saved.content
    assert saved.structured_resume == _snapshot()
    assert saved.explanation == "Explanation"
