from threading import Barrier, Lock, current_thread

from acd.infrastructure.linkedin.linkedin_saved_jobs_browser import SavedLinkedInJob
from acd.services.linkedin_job_import_service import ImportedLinkedInJob
from acd.services.linkedin_saved_jobs_import_service import LinkedInSavedJobsImportService
from acd.services.salary_research_service import SalaryResearchResult


class Browser:
    def collect_saved_jobs(self, **_kwargs):
        return [
            SavedLinkedInJob("https://www.linkedin.com/jobs/view/1234567/", "1234567", "Cargo", "Acme", "São Paulo, SP"),
            SavedLinkedInJob("https://www.linkedin.com/jobs/view/7654321/", "7654321", "Outro", "Acme", "São Paulo, SP"),
        ]


class Importer:
    def import_from_url(self, url):
        return ImportedLinkedInJob(
            title="Cargo",
            company_name="Acme",
            location="São Paulo, SP",
            source_url=url,
        )


class JobService:
    def __init__(self):
        self.created = []

    def job_url_exists(self, url):
        return url.endswith("7654321/")

    def create_job(self, **kwargs):
        self.created.append(kwargs)


class Company:
    id = 10
    name = "Acme"


class CompanyService:
    def list_companies(self):
        return [Company()]

    def create_company(self, **_kwargs):
        raise AssertionError("company should already exist")


def test_import_saved_jobs_imports_and_skips_duplicates():
    jobs = JobService()
    service = LinkedInSavedJobsImportService(Browser(), Importer(), jobs, CompanyService())
    result = service.import_saved_jobs()

    assert result.found == 2
    assert result.imported == 1
    assert result.existing == 1
    assert result.failed == 0
    assert jobs.created[0]["company_id"] == 10
    assert jobs.created[0]["status"] == "Nova"


class ClosedBrowser:
    def collect_saved_jobs(self, **_kwargs):
        return [
            SavedLinkedInJob(
                "https://www.linkedin.com/jobs/view/1234567/",
                "1234567",
                "Cargo encerrado",
                "Acme",
                "São Paulo, SP",
                accepting_applications=False,
            )
        ]


class ExistingJob:
    id = 99


class JobRepository:
    def __init__(self):
        self.deleted = []

    def get_by_url(self, url):
        assert url.endswith("1234567/")
        return ExistingJob()

    def get_by_linkedin_job_id(self, _linkedin_job_id):
        raise AssertionError("exact URL should be found first")

    def delete(self, job_id, *, delete_linked=False):
        self.deleted.append((job_id, delete_linked))
        return True


def test_import_saved_jobs_deletes_closed_existing_job():
    jobs = JobService()
    repository = JobRepository()
    service = LinkedInSavedJobsImportService(
        ClosedBrowser(),
        Importer(),
        jobs,
        CompanyService(),
        repository,
    )

    result = service.import_saved_jobs()

    assert result.found == 1
    assert result.imported == 0
    assert result.existing == 0
    assert result.deleted == 1
    assert result.failed == 0
    assert repository.deleted == [(99, True)]
    assert jobs.created == []


class IncrementalBrowser:
    def __init__(self) -> None:
        self.excluded_job_ids = None

    def collect_saved_jobs(self, **kwargs):
        self.excluded_job_ids = kwargs["excluded_job_ids"]
        return []


class IncrementalRepository:
    def get_linkedin_job_ids(self):
        return {"1234567", "7654321"}


def test_import_saved_jobs_passes_processed_ids_to_browser():
    browser = IncrementalBrowser()
    service = LinkedInSavedJobsImportService(
        browser,
        Importer(),
        JobService(),
        CompanyService(),
        IncrementalRepository(),
    )

    result = service.import_saved_jobs()

    assert browser.excluded_job_ids == {"1234567", "7654321"}
    assert result.found == 0


class EnrichedBrowser:
    def collect_saved_jobs(self, **_kwargs):
        return [
            SavedLinkedInJob(
                "https://www.linkedin.com/jobs/view/9999999/",
                "9999999",
                "Coordenador de Logística",
                "Acme",
                "Guarulhos, SP",
                accepting_applications=True,
                work_model="Híbrido",
                employment_type="",
                salary_min=7000,
                salary_max=9000,
                currency="BRL",
            )
        ]


class EmptyMetadataImporter:
    def import_from_url(self, url):
        return ImportedLinkedInJob(
            title="Coordenador de Logística",
            company_name="Acme",
            location="Guarulhos, SP",
            source_url=url,
        )


def test_import_saved_jobs_uses_page_metadata_and_defaults_to_clt():
    jobs = JobService()
    service = LinkedInSavedJobsImportService(
        EnrichedBrowser(),
        EmptyMetadataImporter(),
        jobs,
        CompanyService(),
    )

    result = service.import_saved_jobs()

    assert result.imported == 1
    created = jobs.created[0]
    assert created["work_model"] == "Híbrido"
    assert created["employment_type"] == "CLT"
    assert created["salary_min"] == 9000
    assert created["salary_max"] is None
    assert created["currency"] == "BRL"



class SalaryResearch:
    def __init__(self) -> None:
        self.requests = []

    def research(self, request):
        self.requests.append(request)
        return SalaryResearchResult(
            salary_min=8500,
            salary_max=10500,
            currency="BRL",
            period="mensal",
            confidence="média",
            geographic_scope="cidade",
            summary="",
            sources=(),
        )


class NoSalaryBrowser:
    def collect_saved_jobs(self, **_kwargs):
        return [
            SavedLinkedInJob(
                "https://www.linkedin.com/jobs/view/3333333/",
                "3333333",
                "Supervisor de Logística",
                "Acme",
                "Guarulhos, SP",
                accepting_applications=True,
                work_model="Presencial",
                employment_type="CLT",
            )
        ]


class NoSalaryImporter:
    def import_from_url(self, url):
        return ImportedLinkedInJob(
            title="Supervisor de Logística",
            company_name="Acme",
            location="Guarulhos, SP",
            work_model="Presencial",
            employment_type="CLT",
            source_url=url,
        )


def test_import_saved_jobs_completes_missing_salary_with_ai():
    jobs = JobService()
    salary_research = SalaryResearch()
    service = LinkedInSavedJobsImportService(
        NoSalaryBrowser(),
        NoSalaryImporter(),
        jobs,
        CompanyService(),
        salary_research_service=salary_research,
    )

    result = service.import_saved_jobs()

    assert result.imported == 1
    assert len(salary_research.requests) == 1
    request = salary_research.requests[0]
    assert request.title == "Supervisor de Logística"
    assert request.location == "Guarulhos, SP"
    assert request.work_model == "Presencial"
    assert request.employment_type == "CLT"
    assert jobs.created[0]["salary_min"] is None
    assert jobs.created[0]["salary_max"] == 10500
    assert jobs.created[0]["currency"] == "BRL"


def test_import_saved_jobs_preserves_advertised_remuneration_and_researches_ideal():
    jobs = JobService()
    salary_research = SalaryResearch()
    service = LinkedInSavedJobsImportService(
        EnrichedBrowser(),
        EmptyMetadataImporter(),
        jobs,
        CompanyService(),
        salary_research_service=salary_research,
    )

    result = service.import_saved_jobs()

    assert result.imported == 1
    assert len(salary_research.requests) == 1
    assert jobs.created[0]["salary_min"] == 9000
    assert jobs.created[0]["salary_max"] == 10500



class ParallelSalaryBrowser:
    def collect_saved_jobs(self, **_kwargs):
        return [
            SavedLinkedInJob(
                f"https://www.linkedin.com/jobs/view/444444{index}/",
                f"444444{index}",
                f"Analista de Logística {index}",
                "Acme",
                "Guarulhos, SP",
                accepting_applications=True,
                work_model="Híbrido",
                employment_type="CLT",
            )
            for index in range(3)
        ]


class ParallelImporter:
    def import_from_url(self, url):
        job_id = url.rstrip("/").split("/")[-1]
        return ImportedLinkedInJob(
            title=f"Analista de Logística {job_id[-1]}",
            company_name="Acme",
            location="Guarulhos, SP",
            work_model="Híbrido",
            employment_type="CLT",
            source_url=url,
        )


class ParallelSalaryResearch:
    def __init__(self) -> None:
        self.barrier = Barrier(3)
        self.lock = Lock()
        self.thread_names = set()

    def research(self, _request):
        with self.lock:
            self.thread_names.add(current_thread().name)
        self.barrier.wait(timeout=3)
        return SalaryResearchResult(
            salary_min=7000,
            salary_max=9000,
            currency="BRL",
        )


def test_import_saved_jobs_researches_missing_salaries_in_parallel():
    jobs = JobService()
    salary_research = ParallelSalaryResearch()
    service = LinkedInSavedJobsImportService(
        ParallelSalaryBrowser(),
        ParallelImporter(),
        jobs,
        CompanyService(),
        salary_research_service=salary_research,
    )

    result = service.import_saved_jobs()

    assert result.imported == 3
    assert len(salary_research.thread_names) == 3
    assert all(job["salary_min"] is None for job in jobs.created)
    assert all(job["salary_max"] == 9000 for job in jobs.created)


class RecruiterEmailResearch:
    def __init__(self, result: str) -> None:
        self.result = result
        self.requests = []

    def research(self, request):
        self.requests.append(request)
        return self.result


class PublicEmailBrowser:
    def collect_saved_jobs(self, **_kwargs):
        return [
            SavedLinkedInJob(
                "https://www.linkedin.com/jobs/view/5555555/",
                "5555555",
                "Analista",
                "Acme",
                "São Paulo, SP",
                accepting_applications=True,
                recruiter_email="rh@acme.com.br",
            )
        ]


def test_import_saved_jobs_prefers_public_email_from_vacancy() -> None:
    jobs = JobService()
    email_research = RecruiterEmailResearch("pesquisado@acme.com.br")
    service = LinkedInSavedJobsImportService(
        PublicEmailBrowser(),
        Importer(),
        jobs,
        CompanyService(),
        recruiter_email_research_service=email_research,
    )

    result = service.import_saved_jobs()

    assert result.imported == 1
    assert jobs.created[0]["recruiter_email"] == "rh@acme.com.br"
    assert email_research.requests == []


def test_import_saved_jobs_researches_recruiter_email_when_missing() -> None:
    jobs = JobService()
    email_research = RecruiterEmailResearch("talentos@acme.com.br")
    service = LinkedInSavedJobsImportService(
        NoSalaryBrowser(),
        NoSalaryImporter(),
        jobs,
        CompanyService(),
        recruiter_email_research_service=email_research,
    )

    result = service.import_saved_jobs()

    assert result.imported == 1
    assert jobs.created[0]["recruiter_email"] == "talentos@acme.com.br"
    assert len(email_research.requests) == 1

