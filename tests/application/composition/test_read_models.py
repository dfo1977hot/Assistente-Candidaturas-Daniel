from __future__ import annotations

from dataclasses import asdict

from acd.application.composition.read_models import (
    ApplicationContext,
    ATSContext,
    CompanyContext,
    GapContext,
    InterviewContext,
    ResumeContext,
    VacancyContext,
)
from acd.application.structured_resume_snapshot import StructuredResumeSnapshotCodec


def test_interview_context_is_a_serializable_read_only_snapshot() -> None:
    """Composition contracts carry context without business behavior."""
    context = InterviewContext(
        application=ApplicationContext(1, 2, 3, "Entrevista Técnica"),
        vacancy=VacancyContext(2, "Backend", ("Python",)),
        company=CompanyContext(3, "ACD", "Tecnologia"),
        resume=ResumeContext(4, "v1.0", "Python, SQL"),
        identified_competencies=("Python",),
        ats_result=ATSContext(80.0, ("Destacar Python.",)),
        gaps=GapContext(("Docker",), ()),
        related_history=({"event": "interview_scheduled"},),
    )

    assert asdict(context)["ats_result"]["total_score"] == 80.0
    assert context.gaps is not None
    assert context.gaps.missing_skills == ("Docker",)


def test_resume_context_preserves_an_optional_immutable_structured_snapshot() -> None:
    snapshot = StructuredResumeSnapshotCodec().from_payload(
        {
            "schema_version": 1,
            "identity": {"full_name": None, "professional_title": None, "location": None},
            "contact": {"email": None, "phone": None, "linkedin": None, "portfolio": None, "website": None},
            "summary": None, "skills": [], "experiences": [], "education": [], "certifications": [],
            "courses": [], "languages": [], "projects": [], "additional_sections": [],
        }
    )

    context = ResumeContext(1, "v1", "legacy description", snapshot)

    assert context.curriculum_id == 1
    assert context.description == "legacy description"
    assert context.structured_resume is snapshot
