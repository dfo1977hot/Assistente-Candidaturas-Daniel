"""Tests for ApplicationService."""

from __future__ import annotations

from datetime import date

import pytest

from acd.domain.entities.application import Application
from acd.services.application_service import ApplicationService


class FakeRepository:
    """Fake repository."""

    def __init__(self) -> None:
        self.items: dict[int, Application] = {}
        self.events: dict[int, list[tuple[str, str]]] = {}

    def create(self, application: Application) -> Application:
        application.id = len(self.items) + 1
        self.items[application.id] = application
        return application

    def update(self, application: Application) -> Application:
        self.items[application.id] = application
        return application

    def delete(self, application_id: int) -> bool:
        return self.items.pop(application_id, None) is not None

    def get_by_id(self, application_id: int) -> Application | None:
        return self.items.get(application_id)

    def get_all(self) -> list[Application]:
        return list(self.items.values())

    def search(self, query: str) -> list[Application]:
        return [
            app
            for app in self.items.values()
            if query.lower() in (app.notes or "").lower()
            or query.lower() in (app.status or "").lower()
        ]

    def filter(
        self,
        *,
        status=None,
        company_id=None,
        channel=None,
    ) -> list[Application]:
        result = list(self.items.values())

        if status is not None:
            result = [a for a in result if a.status == status]

        if company_id is not None:
            result = [a for a in result if a.company_id == company_id]

        if channel is not None:
            result = [a for a in result if a.application_channel == channel]

        return result

    def change_status(
        self,
        application_id: int,
        status: str,
    ) -> Application | None:
        app = self.items.get(application_id)

        if app is not None:
            app.status = status

        return app

    def add_event(
        self,
        application_id: int,
        event_type: str,
        description: str,
    ) -> None:
        self.events.setdefault(application_id, []).append(
            (
                event_type,
                description,
            )
        )

    def get_followups(self, application_id: int):
        return self.events.get(application_id, [])

    def get_statistics(self):
        return {
            "applications": len(self.items),
        }


def create_service() -> ApplicationService:
    return ApplicationService(repository=FakeRepository())


# ==========================================================
# create_application
# ==========================================================


def test_create_application_defaults() -> None:
    service = create_service()

    application = service.create_application(
        job_id=1,
        company_id=1,
    )

    assert application.id == 1
    assert application.status == "Rascunho"
    assert application.job_id == 1
    assert application.company_id == 1


def test_create_application_complete() -> None:
    service = create_service()

    application = service.create_application(
        job_id=2,
        company_id=3,
        status="Aplicada",
        application_date="2026-07-01",
        next_follow_up="2026-07-05",
        response_date="2026-07-10",
        interview_date="2026-07-15",
        salary_expected=18000,
        salary_offered=17500,
        application_channel="LinkedIn",
        recruiter_name="Maria",
        recruiter_email="maria@email.com",
        recruiter_phone="11999999999",
        feedback="Excelente",
        notes="Observação",
    )

    assert application.status == "Aplicada"
    assert application.application_date == date(2026, 7, 1)
    assert application.salary_expected == 18000
    assert application.application_channel == "LinkedIn"


def test_create_application_invalid_job() -> None:
    service = create_service()

    with pytest.raises(ValueError):
        service.create_application(
            job_id=0,
            company_id=1,
        )


def test_create_application_invalid_company() -> None:
    service = create_service()

    with pytest.raises(ValueError):
        service.create_application(
            job_id=1,
            company_id=0,
        )


def test_create_application_invalid_status() -> None:
    service = create_service()

    with pytest.raises(ValueError):
        service.create_application(
            job_id=1,
            company_id=1,
            status="ABC",
        )


# ==========================================================
# update_application
# ==========================================================


def test_update_application() -> None:
    service = create_service()

    application = service.create_application(
        job_id=1,
        company_id=1,
    )

    updated = service.update_application(
        application.id,
        job_id=2,
        company_id=3,
        status="Preparando Currículo",
        notes="Atualizado",
    )

    assert updated is not None
    assert updated.job_id == 2
    assert updated.company_id == 3
    assert updated.notes == "Atualizado"


def test_update_application_not_found() -> None:
    service = create_service()

    result = service.update_application(
        999,
        job_id=1,
        company_id=1,
    )

    assert result is None


def test_update_application_invalid_transition() -> None:
    service = create_service()

    application = service.create_application(
        job_id=1,
        company_id=1,
    )

    with pytest.raises(ValueError):
        service.update_application(
            application.id,
            job_id=1,
            company_id=1,
            status="Contratada",
        )


def test_update_application_same_status() -> None:
    service = create_service()

    application = service.create_application(
        job_id=1,
        company_id=1,
    )

    updated = service.update_application(
        application.id,
        job_id=1,
        company_id=1,
        status="Rascunho",
    )

    assert updated is not None


# ==========================================================
# delete_application
# ==========================================================


def test_delete_application() -> None:
    service = create_service()

    application = service.create_application(
        job_id=1,
        company_id=1,
    )

    assert service.delete_application(application.id) is True


def test_delete_application_not_found() -> None:
    service = create_service()

    assert service.delete_application(999) is False

# ==========================================================
# get_application
# ==========================================================


def test_get_application() -> None:
    service = create_service()

    application = service.create_application(
        job_id=1,
        company_id=1,
    )

    found = service.get_application(application.id)

    assert found is application


def test_get_application_not_found() -> None:
    service = create_service()

    assert service.get_application(999) is None


# ==========================================================
# list_applications
# ==========================================================


def test_list_applications() -> None:
    service = create_service()

    service.create_application(job_id=1, company_id=1)
    service.create_application(job_id=2, company_id=2)

    result = service.list_applications()

    assert len(result) == 2


# ==========================================================
# search_applications
# ==========================================================


def test_search_applications_by_notes() -> None:
    service = create_service()

    service.create_application(
        job_id=1,
        company_id=1,
        notes="Python Backend",
    )

    result = service.search_applications("python")

    assert len(result) == 1


def test_search_applications_empty() -> None:
    service = create_service()

    result = service.search_applications("java")

    assert result == []


# ==========================================================
# filter_applications
# ==========================================================


def test_filter_by_status() -> None:
    service = create_service()

    service.create_application(
        job_id=1,
        company_id=1,
        status="Aplicada",
    )

    service.create_application(
        job_id=2,
        company_id=2,
    )

    result = service.filter_applications(
        status="Aplicada",
    )

    assert len(result) == 1


def test_filter_by_company() -> None:
    service = create_service()

    service.create_application(
        job_id=1,
        company_id=10,
    )

    service.create_application(
        job_id=2,
        company_id=20,
    )

    result = service.filter_applications(
        company_id=20,
    )

    assert len(result) == 1
    assert result[0].company_id == 20


def test_filter_by_channel() -> None:
    service = create_service()

    service.create_application(
        job_id=1,
        company_id=1,
        application_channel="LinkedIn",
    )

    service.create_application(
        job_id=2,
        company_id=1,
        application_channel="Indeed",
    )

    result = service.filter_applications(
        channel="Indeed",
    )

    assert len(result) == 1
    assert result[0].application_channel == "Indeed"


# ==========================================================
# change_status
# ==========================================================


def test_change_status() -> None:
    service = create_service()

    application = service.create_application(
        job_id=1,
        company_id=1,
    )

    updated = service.change_status(
        application.id,
        "Preparando Currículo",
    )

    assert updated is not None
    assert updated.status == "Preparando Currículo"


def test_change_status_administrative() -> None:
    service = create_service()

    application = service.create_application(
        job_id=1,
        company_id=1,
    )

    updated = service.change_status(
        application.id,
        "Contratada",
        administrative=True,
    )

    assert updated.status == "Contratada"


def test_change_status_invalid_transition() -> None:
    service = create_service()

    application = service.create_application(
        job_id=1,
        company_id=1,
    )

    with pytest.raises(ValueError):
        service.change_status(
            application.id,
            "Contratada",
        )


def test_change_status_not_found() -> None:
    service = create_service()

    assert service.change_status(
        999,
        "Aplicada",
    ) is None


def test_change_status_invalid_status() -> None:
    service = create_service()

    application = service.create_application(
        job_id=1,
        company_id=1,
    )

    with pytest.raises(ValueError):
        service.change_status(
            application.id,
            "INVALID",
        )


# ==========================================================
# followups / statistics
# ==========================================================


def test_get_followups() -> None:
    service = create_service()

    application = service.create_application(
        job_id=1,
        company_id=1,
    )

    service.change_status(
        application.id,
        "Preparando Currículo",
    )

    followups = service.get_followups(application.id)

    assert len(followups) >= 2


def test_get_statistics() -> None:
    service = create_service()

    service.create_application(
        job_id=1,
        company_id=1,
    )

    stats = service.get_statistics()

    assert stats["applications"] == 1


# ==========================================================
# validators
# ==========================================================


def test_validate_required_fields() -> None:
    service = create_service()

    service._validate_required_fields(
        job_id=1,
        company_id=1,
    )


def test_validate_required_fields_invalid_job() -> None:
    service = create_service()

    with pytest.raises(ValueError):
        service._validate_required_fields(
            job_id=0,
            company_id=1,
        )


def test_validate_required_fields_invalid_company() -> None:
    service = create_service()

    with pytest.raises(ValueError):
        service._validate_required_fields(
            job_id=1,
            company_id=0,
        )


def test_validate_status() -> None:
    service = create_service()

    service._validate_status("Aplicada")


def test_validate_status_invalid() -> None:
    service = create_service()

    with pytest.raises(ValueError):
        service._validate_status("ABC")


def test_validate_transition() -> None:
    service = create_service()

    service._validate_transition(
        "Rascunho",
        "Preparando Currículo",
    )


def test_validate_transition_administrative() -> None:
    service = create_service()

    service._validate_transition(
        "Rascunho",
        "Contratada",
        administrative=True,
    )


def test_validate_transition_invalid() -> None:
    service = create_service()

    with pytest.raises(ValueError):
        service._validate_transition(
            "Rascunho",
            "Contratada",
        )


# ==========================================================
# parse_optional_date
# ==========================================================


def test_parse_optional_date() -> None:
    service = create_service()

    assert service._parse_optional_date(
        "2026-07-01",
    ) == date(
        2026,
        7,
        1,
    )


def test_parse_optional_date_none() -> None:
    service = create_service()

    assert service._parse_optional_date(None) is None


def test_parse_optional_date_empty() -> None:
    service = create_service()

    assert service._parse_optional_date("") is None