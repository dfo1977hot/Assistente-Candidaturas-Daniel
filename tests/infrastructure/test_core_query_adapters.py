from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from acd.infrastructure.query_adapters.company_query_adapter import CompanyQueryAdapter
from acd.infrastructure.query_adapters.resume_query_adapter import ResumeQueryAdapter
from acd.infrastructure.query_adapters.vacancy_query_adapter import VacancyQueryAdapter


class FakeResumeRepository:
    """Read-only curriculum repository double for adapter tests."""

    def __init__(self, curriculum: object | None, versions: list[object]) -> None:
        self._curriculum = curriculum
        self._versions = versions

    def get_by_id(self, curriculum_id: int) -> object | None:
        return self._curriculum

    def get_versions(self, curriculum_id: int) -> list[object]:
        return self._versions


class FakeCompanyRepository:
    """Read-only company repository double for adapter tests."""

    def __init__(self, company: object | None) -> None:
        self._company = company

    def get_by_id(self, company_id: int) -> object | None:
        return self._company


class FakeJobRepository:
    """Read-only vacancy repository double for adapter tests."""

    def __init__(self, job: object | None) -> None:
        self._job = job

    def get_by_id(self, job_id: int) -> object | None:
        return self._job


class FakeJobProfileRepository:
    """Read-only job profile repository double for adapter tests."""

    def __init__(self, profile: object | None) -> None:
        self._profile = profile

    def get_by_job(self, job_id: int) -> object | None:
        return self._profile


def test_resume_query_adapter_maps_curriculum_and_versions() -> None:
    """Curriculum entities are projected as immutable query DTOs."""
    now = datetime.now(UTC)
    adapter = ResumeQueryAdapter(
        FakeResumeRepository(
            SimpleNamespace(id=1, name="Base", version="v1.0", language="pt-BR", description="SQL"),
            [SimpleNamespace(id=2, curriculum_id=1, version="v1.0", file_name="cv.pdf", created_at=now)],
        )
    )

    assert adapter.get_by_id(1) is not None
    assert adapter.list_versions(1)[0].file_name == "cv.pdf"


def test_company_and_vacancy_query_adapters_map_available_data() -> None:
    """Company and vacancy repository entities are not exposed to consumers."""
    company_adapter = CompanyQueryAdapter(FakeCompanyRepository(SimpleNamespace(id=3, name="ACD", segment="Tecnologia")))
    vacancy_adapter = VacancyQueryAdapter(
        FakeJobRepository(SimpleNamespace(id=4, title="Backend", company_id=3, notes="Remoto")),
        FakeJobProfileRepository(SimpleNamespace(raw_description="Python obrigatório", skills="Python, Docker")),
    )

    assert company_adapter.get_by_id(3) is not None
    assert vacancy_adapter.get_by_id(4).competencies == ("Python", "Docker")


def test_core_query_adapters_return_none_or_empty_for_missing_data() -> None:
    """Missing repository entities remain absent from public query contracts."""
    assert ResumeQueryAdapter(FakeResumeRepository(None, [])).get_by_id(1) is None
    assert CompanyQueryAdapter(FakeCompanyRepository(None)).get_by_id(1) is None
    assert VacancyQueryAdapter(FakeJobRepository(None), FakeJobProfileRepository(None)).get_by_id(1) is None
