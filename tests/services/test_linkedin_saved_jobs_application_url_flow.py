from acd.infrastructure.linkedin.linkedin_saved_jobs_browser import SavedLinkedInJob
from acd.services.linkedin_saved_jobs_import_service import LinkedInSavedJobsImportService


class ExistingJob:
    id = 7
    application_url = ""


class Repository:
    def __init__(self):
        self.job = ExistingJob()
        self.updated = []
        self.deleted = []

    def get_by_url(self, _url):
        return self.job

    def get_by_linkedin_job_id(self, _linkedin_job_id):
        return self.job

    def update(self, job):
        self.updated.append(job)
        return job

    def delete(self, job_id, *, delete_linked=False):
        self.deleted.append((job_id, delete_linked))
        return True


class Jobs:
    def __init__(self):
        self.created = []

    def job_url_exists(self, _url):
        return False

    def create_job(self, **kwargs):
        self.created.append(kwargs)


class Companies:
    class Company:
        id = 1
        name = "Acme"

    def list_companies(self):
        return [self.Company()]


class Importer:
    def import_from_url(self, url):
        from acd.services.linkedin_job_import_service import ImportedLinkedInJob

        return ImportedLinkedInJob(
            title="Cargo",
            company_name="Acme",
            source_url=url,
            accepting_applications=True,
        )


class Browser:
    def __init__(self, reference):
        self.reference = reference

    def collect_saved_jobs(self, **_kwargs):
        return [self.reference]


def test_new_import_persists_detected_application_url() -> None:
    application_url = "https://empresa.gupy.io/jobs/123"
    reference = SavedLinkedInJob(
        "https://www.linkedin.com/jobs/view/123/",
        "123",
        "Cargo",
        "Acme",
        application_url=application_url,
        accepting_applications=True,
    )
    jobs = Jobs()
    service = LinkedInSavedJobsImportService(
        Browser(reference),
        Importer(),
        jobs,
        Companies(),
    )

    result = service.import_saved_jobs()

    assert result.imported == 1
    assert jobs.created[0]["application_url"] == application_url


def test_equal_job_and_application_urls_are_treated_as_closed() -> None:
    url = "https://www.linkedin.com/jobs/view/123/"
    reference = SavedLinkedInJob(
        url,
        "123",
        "Cargo",
        "Acme",
        application_url=url,
        accepting_applications=True,
    )
    repository = Repository()
    service = LinkedInSavedJobsImportService(
        Browser(reference),
        Importer(),
        Jobs(),
        Companies(),
        repository,
    )

    result = service.import_saved_jobs()

    assert result.imported == 0
    assert result.deleted == 1
    assert repository.deleted == [(7, True)]
