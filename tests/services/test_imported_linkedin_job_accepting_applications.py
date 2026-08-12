from acd.services.linkedin_job_import_service import ImportedLinkedInJob


def test_accepting_applications_defaults_to_unknown() -> None:
    job = ImportedLinkedInJob(title="Cargo")
    assert job.accepting_applications is None


def test_accepting_applications_can_mark_closed_job() -> None:
    job = ImportedLinkedInJob(
        title="Cargo",
        accepting_applications=False,
    )
    assert job.accepting_applications is False
