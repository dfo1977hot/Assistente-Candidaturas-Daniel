from pathlib import Path

from acd.services.closed_linkedin_jobs_registry import ClosedLinkedInJobsRegistry
from acd.services.linkedin_job_import_service import LinkedInJobImportService


def test_constructor_accepts_closed_jobs_registry(tmp_path: Path) -> None:
    registry = ClosedLinkedInJobsRegistry(tmp_path / "closed.json")
    service = LinkedInJobImportService(
        api_key="test",
        closed_jobs_registry=registry,
    )
    assert service._closed_jobs_registry is registry


def test_permanently_closed_job_is_returned_as_closed_without_api_call(
    tmp_path: Path,
) -> None:
    registry = ClosedLinkedInJobsRegistry(tmp_path / "closed.json")
    registry.mark_closed("123456789")
    service = LinkedInJobImportService(
        api_key="test",
        closed_jobs_registry=registry,
    )

    result = service.import_from_url(
        "https://www.linkedin.com/jobs/view/cargo-123456789/"
    )

    assert result.linkedin_job_id == "123456789"
    assert result.accepting_applications is False
