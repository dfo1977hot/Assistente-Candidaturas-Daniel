from __future__ import annotations

from datetime import date
from types import SimpleNamespace

from acd.services.application_service import ApplicationService
from acd.services.job_service import JobService


class _ApplicationRepository:
    def __init__(self) -> None:
        self.application = SimpleNamespace(
            id=1,
            status="Aplicada",
            application_date=date(2026, 8, 8),
            next_follow_up=date(2026, 8, 12),
        )

    def get_by_id(self, application_id: int):
        return self.application if application_id == 1 else None

    def change_status(
        self,
        application_id: int,
        status: str,
        *,
        clear_application_dates: bool = False,
    ):
        assert application_id == 1
        self.application.status = status
        if clear_application_dates:
            self.application.application_date = None
            self.application.next_follow_up = None
        return self.application

    def add_event(self, *_args, **_kwargs) -> None:
        return None


class _JobRepository:
    def __init__(self) -> None:
        self.created = None

    def url_exists(self, *_args, **_kwargs) -> bool:
        return False

    def create(self, job):
        job.id = 1
        self.created = job
        return job


def test_applied_can_return_to_ready_and_clears_dates() -> None:
    repository = _ApplicationRepository()
    service = ApplicationService(repository=repository)

    updated = service.change_status(1, "Pronta para Aplicação")

    assert updated is not None
    assert updated.status == "Pronta para Aplicação"
    assert updated.application_date is None
    assert updated.next_follow_up is None


def test_job_service_persists_external_application_url() -> None:
    repository = _JobRepository()
    service = JobService(repository=repository)

    created = service.create_job(
        company_id=1,
        title="Gerente de Logística",
        job_url="https://www.linkedin.com/jobs/view/123/",
        application_url="https://empresa.example/carreiras/123",
    )

    assert created.application_url == "https://empresa.example/carreiras/123"
