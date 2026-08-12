from pathlib import Path

from acd.services.closed_linkedin_jobs_registry import ClosedLinkedInJobsRegistry


def test_closed_registry_persists_ids(tmp_path: Path) -> None:
    path = tmp_path / "closed.json"
    registry = ClosedLinkedInJobsRegistry(path)

    registry.mark_closed("1234567")

    assert registry.contains("1234567")
    assert ClosedLinkedInJobsRegistry(path).ids() == {"1234567"}


def test_closed_registry_extracts_linkedin_id() -> None:
    registry = ClosedLinkedInJobsRegistry(Path("unused.json"))
    assert registry.job_id_from_url(
        "https://www.linkedin.com/jobs/view/cargo-4450923501/"
    ) == "4450923501"
