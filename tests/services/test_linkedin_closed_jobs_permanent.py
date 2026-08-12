from pathlib import Path

from acd.infrastructure.linkedin.linkedin_saved_jobs_browser import SavedLinkedInJob
from acd.services.closed_linkedin_jobs_registry import ClosedLinkedInJobsRegistry
from acd.services.linkedin_saved_jobs_import_service import LinkedInSavedJobsImportService


class Browser:
    def __init__(self) -> None:
        self.kwargs = {}

    def collect_saved_jobs(self, **kwargs):
        self.kwargs = kwargs
        return [
            SavedLinkedInJob(
                "https://www.linkedin.com/jobs/view/1234567/",
                "1234567",
                "Vaga encerrada",
                "Acme",
                "São Paulo, SP",
                accepting_applications=False,
            )
        ]


class Importer:
    def import_from_url(self, _url):
        raise AssertionError("vaga encerrada não deve ser importada")


class JobService:
    def job_url_exists(self, _url):
        return False

    def create_job(self, **_kwargs):
        raise AssertionError("vaga encerrada não deve ser criada")


class CompanyService:
    def list_companies(self):
        return []


class ExistingJob:
    id = 99


class Repository:
    def get_linkedin_job_ids(self):
        return {"7654321"}

    def get_by_url(self, _url):
        return ExistingJob()

    def get_by_linkedin_job_id(self, _job_id):
        return None

    def delete(self, job_id, *, delete_linked=False):
        assert job_id == 99
        assert delete_linked is True
        return True


def test_closed_saved_job_is_deleted_and_permanently_registered(tmp_path: Path) -> None:
    registry = ClosedLinkedInJobsRegistry(tmp_path / "closed.json")
    browser = Browser()
    service = LinkedInSavedJobsImportService(
        browser,
        Importer(),
        JobService(),
        CompanyService(),
        Repository(),
        closed_jobs_registry=registry,
    )

    result = service.import_saved_jobs()

    assert result.deleted == 1
    assert result.imported == 0
    assert registry.contains("1234567")
    assert browser.kwargs["excluded_job_ids"] == {"7654321"}
    assert browser.kwargs["permanently_excluded_job_ids"] == set()
