"""Tests for deterministic, read-only effective resume resolution."""

from __future__ import annotations

from datetime import UTC, datetime

from acd.application.application_resume_source import ApplicationResumeSource
from acd.application.composition.read_models import ApplicationContext
from acd.application.effective_application_resume_use_case import (
    EffectiveApplicationResumeRequest,
    EffectiveApplicationResumeStatus,
    EffectiveApplicationResumeUseCase,
)
from acd.application.query_ports import GeneratedResumeVersionQueryDTO, ResumeQueryDTO
from acd.application.structured_resume_snapshot import (
    StructuredResumeContentStatus,
    StructuredResumeSnapshotCodec,
)


class _Applications:
    def __init__(self, context: ApplicationContext | None) -> None:
        self.context = context

    def build(self, application_id: int) -> ApplicationContext | None:
        return self.context


class _Resumes:
    def __init__(self, resume: ResumeQueryDTO | None) -> None:
        self.resume = resume
        self.calls: list[int] = []

    def get_by_id(self, curriculum_id: int) -> ResumeQueryDTO | None:
        self.calls.append(curriculum_id)
        return self.resume


class _Versions:
    def __init__(self, versions: tuple[GeneratedResumeVersionQueryDTO, ...]) -> None:
        self.versions = versions
        self.calls: list[int] = []

    def list_by_curriculum_id(self, curriculum_id: int) -> tuple[GeneratedResumeVersionQueryDTO, ...]:
        self.calls.append(curriculum_id)
        return self.versions


def _context(
    source: ApplicationResumeSource = ApplicationResumeSource.ORIGINAL,
    selected: int | None = None,
    curriculum_id: int | None = 10,
) -> ApplicationContext:
    return ApplicationContext(1, 2, 3, "Draft", curriculum_id, selected, source)


def _resume(content: str = "Currículo original") -> ResumeQueryDTO:
    return ResumeQueryDTO(10, "Daniel", "v1", "pt-BR", content)


def _version(version_id: int, curriculum_id: int = 10, content: str = "Versão adotada") -> GeneratedResumeVersionQueryDTO:
    return GeneratedResumeVersionQueryDTO(
        version_id, curriculum_id, f"v{version_id}", content, "", datetime(2026, 1, 1, tzinfo=UTC)
    )


def _use_case(
    context: ApplicationContext | None,
    resume: ResumeQueryDTO | None = None,
    versions: tuple[GeneratedResumeVersionQueryDTO, ...] = (),
) -> tuple[EffectiveApplicationResumeUseCase, _Resumes, _Versions]:
    resumes = _Resumes(resume or _resume())
    generated = _Versions(versions)
    return EffectiveApplicationResumeUseCase(_Applications(context), resumes, generated), resumes, generated


def test_resolves_original_content_without_querying_generated_versions() -> None:
    use_case, _, versions = _use_case(_context())

    result = use_case.execute(EffectiveApplicationResumeRequest(1))

    assert result.status is EffectiveApplicationResumeStatus.SUCCESS
    assert result.resume_source is ApplicationResumeSource.ORIGINAL
    assert result.effective_resume_version_id is None
    assert result.content == "Currículo original"
    assert versions.calls == []


def test_resolves_only_the_persisted_adopted_version() -> None:
    use_case, _, _ = _use_case(
        _context(ApplicationResumeSource.RESUME_VERSION, 2),
        versions=(_version(2, content="Versão 2"), _version(4, content="Mais recente")),
    )

    result = use_case.execute(EffectiveApplicationResumeRequest(1))

    assert result.effective_resume_version_id == 2
    assert result.content == "Versão 2"
    assert result.title == "Versão v2"


def test_does_not_consider_visualized_or_higher_scored_versions() -> None:
    use_case, _, _ = _use_case(
        _context(ApplicationResumeSource.RESUME_VERSION, 2),
        versions=(_version(2, content="Adotada"), _version(3, content="Visualizada com ATS maior")),
    )

    result = use_case.execute(EffectiveApplicationResumeRequest(1))

    assert result.effective_resume_version_id == 2
    assert result.content == "Adotada"


def test_reports_inconsistent_selection_without_fallback() -> None:
    use_case, _, _ = _use_case(_context(ApplicationResumeSource.RESUME_VERSION, None))

    result = use_case.execute(EffectiveApplicationResumeRequest(1))

    assert result.status is EffectiveApplicationResumeStatus.SELECTION_INCONSISTENT
    assert result.content == ""


def test_reports_missing_application_curriculum_and_content() -> None:
    missing_application, _, _ = _use_case(None)
    missing_curriculum, _, _ = _use_case(_context(curriculum_id=None))
    missing_content, _, _ = _use_case(_context(), _resume(""))

    assert (
        missing_application.execute(EffectiveApplicationResumeRequest(1)).status
        is EffectiveApplicationResumeStatus.APPLICATION_NOT_FOUND
    )
    assert (
        missing_curriculum.execute(EffectiveApplicationResumeRequest(1)).status
        is EffectiveApplicationResumeStatus.CURRICULUM_REQUIRED
    )
    assert (
        missing_content.execute(EffectiveApplicationResumeRequest(1)).status
        is EffectiveApplicationResumeStatus.CONTENT_UNAVAILABLE
    )


def test_reports_missing_curriculum_and_selected_version_content() -> None:
    missing_curriculum = EffectiveApplicationResumeUseCase(
        _Applications(_context()),
        _Resumes(None),
        _Versions(()),
    )
    missing_version, _, _ = _use_case(_context(ApplicationResumeSource.RESUME_VERSION, 2))
    missing_content, _, _ = _use_case(
        _context(ApplicationResumeSource.RESUME_VERSION, 2),
        versions=(_version(2, content=""),),
    )

    assert (
        missing_curriculum.execute(EffectiveApplicationResumeRequest(1)).status
        is EffectiveApplicationResumeStatus.CURRICULUM_NOT_FOUND
    )
    assert (
        missing_version.execute(EffectiveApplicationResumeRequest(1)).status
        is EffectiveApplicationResumeStatus.SELECTED_VERSION_NOT_FOUND
    )
    assert (
        missing_content.execute(EffectiveApplicationResumeRequest(1)).status
        is EffectiveApplicationResumeStatus.CONTENT_UNAVAILABLE
    )


def test_reports_missing_or_foreign_selected_version_without_writing() -> None:
    use_case, _, versions = _use_case(
        _context(ApplicationResumeSource.RESUME_VERSION, 2),
        versions=(_version(2, curriculum_id=99),),
    )

    result = use_case.execute(EffectiveApplicationResumeRequest(1))

    assert result.status is EffectiveApplicationResumeStatus.SELECTED_VERSION_CURRICULUM_MISMATCH
    assert versions.calls == [10]


def _structured_resume(company: str, skill: str):
    return StructuredResumeSnapshotCodec().from_payload(
        {
            "schema_version": 1,
            "identity": {"full_name": None, "professional_title": None, "location": None},
            "contact": {"email": None, "phone": None, "linkedin": None, "portfolio": None, "website": None},
            "summary": None,
            "skills": [skill],
            "experiences": [{"company": company, "role": None, "location": None, "start_date": None, "end_date": None, "is_current": False, "summary": None, "achievements": []}],
            "education": [], "certifications": [], "courses": [], "languages": [], "projects": [], "additional_sections": [],
        }
    )


def test_resolves_only_the_adopted_structured_resume_without_merging_original() -> None:
    original = ResumeQueryDTO(
        10, "Daniel", "v1", "pt-BR", "original", _structured_resume("Empresa A", "X"), StructuredResumeContentStatus.AVAILABLE
    )
    adopted = GeneratedResumeVersionQueryDTO(
        2, 10, "v2", "adopted", "", datetime(2026, 1, 1, tzinfo=UTC), _structured_resume("Empresa B", "Y"), StructuredResumeContentStatus.AVAILABLE
    )
    use_case, _, _ = _use_case(
        _context(ApplicationResumeSource.RESUME_VERSION, 2), original, (adopted,)
    )

    result = use_case.execute(EffectiveApplicationResumeRequest(1))

    assert result.structured_content_status is StructuredResumeContentStatus.AVAILABLE
    assert result.structured_resume is adopted.structured_resume
    assert result.structured_resume.skills == ("Y",)
    assert result.structured_resume.experiences[0].company == "Empresa B"


def test_preserves_text_when_adopted_snapshot_is_unavailable_or_invalid() -> None:
    legacy = GeneratedResumeVersionQueryDTO(
        2, 10, "v2", "legacy text", "", datetime(2026, 1, 1, tzinfo=UTC)
    )
    use_case, _, _ = _use_case(
        _context(ApplicationResumeSource.RESUME_VERSION, 2), versions=(legacy,)
    )

    result = use_case.execute(EffectiveApplicationResumeRequest(1))

    assert result.content == "legacy text"
    assert result.structured_resume is None
    assert result.structured_content_status is StructuredResumeContentStatus.UNAVAILABLE


def test_preserves_text_when_adopted_snapshot_is_invalid_or_unsupported() -> None:
    invalid = GeneratedResumeVersionQueryDTO(
        2, 10, "v2", "stored text", "", datetime(2026, 1, 1, tzinfo=UTC), None, StructuredResumeContentStatus.INVALID
    )
    use_case, _, _ = _use_case(
        _context(ApplicationResumeSource.RESUME_VERSION, 2), versions=(invalid,)
    )

    result = use_case.execute(EffectiveApplicationResumeRequest(1))

    assert result.content == "stored text"
    assert result.structured_resume is None
    assert result.structured_content_status is StructuredResumeContentStatus.INVALID
