"""Tests for Application composition services."""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
import json

from acd.application.composition.application_context_service import ApplicationContextService
from acd.application.composition.ats_context_adapter import ATSContextAdapter
from acd.application.composition.interview_context_service import InterviewContextService
from acd.application.composition.resume_context_service import ResumeContextService
from acd.application.query_ports import (
    ApplicationHistoryQueryDTO,
    ApplicationQueryDTO,
    ATSHistoryQueryDTO,
    ATSRecommendationQueryDTO,
    ATSScoreDetailQueryDTO,
    CompanyQueryDTO,
    InterviewQueryDTO,
    ResumeQueryDTO,
    VacancyQueryDTO,
)
from acd.application.structured_resume_snapshot import StructuredResumeSnapshotCodec


class FakeApplicationQueryPort:
    """Application Query Port double."""

    def __init__(self, application: ApplicationQueryDTO | None) -> None:
        self._application = application

    def get_by_id(self, application_id: int) -> ApplicationQueryDTO | None:
        return self._application if application_id == 1 else None

    def list_history(self, application_id: int) -> tuple[ApplicationHistoryQueryDTO, ...]:
        if application_id != 1:
            return ()
        return (
            ApplicationHistoryQueryDTO(
                event_type="created",
                description="Application created",
                created_at=datetime(2026, 7, 23, tzinfo=UTC),
            ),
        )


class FakeResumeQueryPort:
    """Resume Query Port double."""

    def get_by_id(self, curriculum_id: int) -> ResumeQueryDTO | None:
        if curriculum_id != 4:
            return None
        return ResumeQueryDTO(4, "Daniel", "v1", "pt-BR", "Python")


class FakeATSHistoryQueryPort:
    """ATS history Query Port double."""

    def get_latest_for_curriculum(self, curriculum_id: int) -> ATSHistoryQueryDTO | None:
        if curriculum_id != 4:
            return None
        return ATSHistoryQueryDTO(10, 4, None, 82.0, datetime(2026, 7, 23, tzinfo=UTC))


class FakeCompanyQueryPort:
    """Company Query Port double."""

    def get_by_id(self, company_id: int) -> CompanyQueryDTO | None:
        return CompanyQueryDTO(3, "ACD", "Technology") if company_id == 3 else None


class FakeVacancyQueryPort:
    """Vacancy Query Port double."""

    def get_by_id(self, job_id: int) -> VacancyQueryDTO | None:
        if job_id != 2:
            return None
        return VacancyQueryDTO(2, "Backend Engineer", 3, "Remote", competencies=("Python",))


class FakeInterviewQueryPort:
    """Interview Query Port double."""

    def list_by_application(self, application_id: int) -> tuple[InterviewQueryDTO, ...]:
        if application_id != 1:
            return ()
        return (
            InterviewQueryDTO(
                8,
                1,
                datetime(2026, 7, 23, tzinfo=UTC),
                "Technical",
                "Scheduled",
            ),
        )


def _application_dto() -> ApplicationQueryDTO:
    return ApplicationQueryDTO(1, 2, 3, 4, "v1", "Interview")


def _resume_service() -> ResumeContextService:
    return ResumeContextService(
        FakeResumeQueryPort(),
        FakeATSHistoryQueryPort(),
        ATSContextAdapter(),
    )


def test_application_context_service_builds_serializable_read_model() -> None:
    """Application history is projected as serializable primitive values."""
    service = ApplicationContextService(FakeApplicationQueryPort(_application_dto()))

    context = service.build(1)

    assert context is not None
    assert context.curriculum_id == 4
    assert context.history[0]["created_at"] == "2026-07-23T00:00:00+00:00"
    json.dumps(asdict(context))
    assert service.build(99) is None


def test_resume_context_service_uses_only_persisted_query_results() -> None:
    """Resume and ATS contexts are read from their respective Query Ports."""
    service = _resume_service()

    resume = service.build(4)
    ats = service.get_ats_context(4)

    assert resume is not None
    assert resume.description == "Python"
    assert ats is not None
    assert ats.total_score == 82.0
    assert service.build(99) is None
    assert service.get_ats_context(99) is None


def test_resume_context_service_propagates_the_dto_snapshot_without_parsing() -> None:
    snapshot = StructuredResumeSnapshotCodec().from_payload(
        {
            "schema_version": 1,
            "identity": {"full_name": None, "professional_title": None, "location": None},
            "contact": {"email": None, "phone": None, "linkedin": None, "portfolio": None, "website": None},
            "summary": None, "skills": [], "experiences": [], "education": [], "certifications": [],
            "courses": [], "languages": [], "projects": [], "additional_sections": [],
        }
    )

    class _ResumePort(FakeResumeQueryPort):
        def get_by_id(self, curriculum_id: int) -> ResumeQueryDTO | None:
            if curriculum_id != 4:
                return None
            return ResumeQueryDTO(4, "Daniel", "v1", "pt-BR", "text", snapshot)

    context = ResumeContextService(
        _ResumePort(), FakeATSHistoryQueryPort(), ATSContextAdapter()
    ).build(4)

    assert context is not None
    assert context.structured_resume is snapshot
    assert context.description == "text"


def test_resume_context_service_exposes_complete_persisted_ats_result() -> None:
    """Read-only ATS retrieval returns the existing Query Port DTO unchanged."""
    persisted = ATSHistoryQueryDTO(
        10,
        4,
        None,
        82.0,
        datetime(2026, 7, 23, tzinfo=UTC),
        recommendations=(ATSRecommendationQueryDTO("Add Docker", "rule"),),
        score_details=(ATSScoreDetailQueryDTO("technical", 32.0, 40.0, 0.4),),
    )
    service = ResumeContextService(
        FakeResumeQueryPort(),
        FakeATSHistoryQueryPortWithResult(persisted),
        ATSContextAdapter(),
    )

    result = service.get_persisted_ats_result(4)
    ats_context = service.get_ats_context(4)
    gap_context = service.get_gap_context(4)

    assert result is persisted
    assert ats_context is not None
    assert ats_context.recommendations == ("Add Docker",)
    assert ats_context.details == {
        "technical": {"score": 32.0, "max_score": 40.0, "weight": 0.4}
    }
    assert gap_context is None


class FakeATSHistoryQueryPortWithResult:
    """ATS history double that returns one pre-existing complete analysis."""

    def __init__(self, result: ATSHistoryQueryDTO) -> None:
        self._result = result

    def get_latest_for_curriculum(self, curriculum_id: int) -> ATSHistoryQueryDTO | None:
        return self._result if curriculum_id == self._result.curriculum_id else None


def test_interview_context_service_builds_complete_serializable_context() -> None:
    """Interview composition contains only read models and serialized history."""
    application_port = FakeApplicationQueryPort(_application_dto())
    service = InterviewContextService(
        application_port,
        ApplicationContextService(application_port),
        _resume_service(),
        FakeCompanyQueryPort(),
        FakeVacancyQueryPort(),
        FakeInterviewQueryPort(),
    )

    context = service.build(1)

    assert context is not None
    assert context.company.name == "ACD"
    assert context.identified_competencies == ("Python",)
    assert context.ats_result is not None
    assert context.gaps is None
    assert context.related_history[0]["interview_date"] == "2026-07-23T00:00:00+00:00"
    json.dumps(asdict(context))
    assert service.build(99) is None
