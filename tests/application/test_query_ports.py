from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime

from acd.application.query_ports import (
    ApplicationQueryDTO,
    ATSHistoryQueryDTO,
    CompanyQueryDTO,
    InterviewQueryDTO,
    ResumeQueryDTO,
    VacancyQueryDTO,
)


def test_query_dtos_are_immutable_and_serializable() -> None:
    """Query DTOs are stable read-only contracts for composition consumers."""
    now = datetime.now(UTC)
    values = (
        ApplicationQueryDTO(1, 2, 3, 4, "v1.0", "Aplicada"),
        ResumeQueryDTO(4, "Base", "v1.0", "pt-BR", "Python"),
        CompanyQueryDTO(3, "ACD", "Tecnologia"),
        VacancyQueryDTO(2, "Backend", 3, ""),
        ATSHistoryQueryDTO(5, 4, 6, 80.0, now),
        InterviewQueryDTO(7, 1, now, "Técnica", "Agendada"),
    )

    assert asdict(values[0])["application_id"] == 1
    assert values[-1].interview_type == "Técnica"
