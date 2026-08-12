from __future__ import annotations

from types import SimpleNamespace

import pytest

from acd.services.workflow_step_registry import (
    ProductiveWorkflowHandlers,
    WorkflowStepRegistry,
)


class JobServiceStub:
    def __init__(self) -> None:
        self.job = SimpleNamespace(
            id=7,
            company_id=3,
            company=SimpleNamespace(id=3, name="ACME"),
            title="Python Engineer",
            location="São Paulo",
            work_model="Remoto",
            employment_type="CLT",
            salary_min=8000.0,
            salary_max=12000.0,
            currency="BRL",
            status="Nova",
            source="LinkedIn",
            job_url="https://www.linkedin.com/jobs/view/7",
            application_url="",
            recruiter="Ana",
            recruiter_email="ana@example.com",
            application_deadline=None,
            application_date=None,
            priority=0,
            notes="Python SQL",
        )
        self.updates: list[dict[str, object]] = []

    def get_job(self, job_id: int):
        return self.job if job_id == self.job.id else None

    def update_job(self, job_id: int, **values):
        assert job_id == self.job.id
        self.updates.append(values)
        for key, value in values.items():
            setattr(self.job, key, value)
        return self.job


class ApplicationServiceStub:
    def __init__(self) -> None:
        self.applications = []
        self.created = 0

    def list_applications(self):
        return self.applications

    def get_application(self, application_id: int):
        return next((item for item in self.applications if item.id == application_id), None)

    def create_application(self, **values):
        self.created += 1
        application = SimpleNamespace(
            id=11,
            status="Rascunho",
            application_date=None,
            next_follow_up=None,
            interview_date=None,
            recruiter_phone="",
            feedback="",
            notes="",
            **values,
        )
        self.applications.append(application)
        return application

    def update_application(self, application_id: int, **values):
        application = self.get_application(application_id)
        for key, value in values.items():
            setattr(application, key, value)
        return application


class CurriculumServiceStub:
    def __init__(self) -> None:
        self.curriculum = SimpleNamespace(
            id=5,
            name="Principal",
            version="v1.0",
            description="Python",
            structured_content_json=None,
            language="pt-BR",
        )

    def list_curricula(self):
        return [self.curriculum]

    def associate_to_application(self, **_values):
        return None

    def create_optimized_curriculum(self, *, source_curriculum_id: int):
        assert source_curriculum_id == 5
        return SimpleNamespace(id=6, version="v1.1")


@pytest.fixture
def dependencies():
    job_service = JobServiceStub()
    application_service = ApplicationServiceStub()
    curriculum_service = CurriculumServiceStub()
    salary_service = SimpleNamespace(
        research=lambda _request: SimpleNamespace(salary_max=15000.0, currency="BRL")
    )
    resolver = SimpleNamespace(
        resolve_linkedin_application_url=lambda _url: SimpleNamespace(
            url="https://www.linkedin.com/jobs/view/7/apply/?trackingId=abc",
            application_type="easy_apply",
            accepting_applications=True,
        )
    )
    handlers = ProductiveWorkflowHandlers(
        job_service=job_service,
        application_service=application_service,
        company_service=SimpleNamespace(),
        company_lookup_service=SimpleNamespace(),
        salary_research_service=salary_service,
        resume_match_service=SimpleNamespace(),
        curriculum_service=curriculum_service,
        cover_letter_service=SimpleNamespace(
            generate_letter=lambda **_values: SimpleNamespace(id=9, version="V1.1")
        ),
        application_url_resolver=resolver,
    )
    return handlers, job_service, application_service


def test_registry_resolves_productive_handlers(dependencies) -> None:
    handlers, _, _ = dependencies
    registry = handlers.registry()
    assert isinstance(registry, WorkflowStepRegistry)
    for command in (
        "verify_job",
        "detect_application_url",
        "enrich_company",
        "research_salary",
        "analyze_fit",
        "select_resume",
        "generate_resume",
        "generate_cover_letter",
        "register_application",
    ):
        assert registry.resolve(command) is not None


def test_salary_handler_changes_only_ideal_salary(dependencies) -> None:
    handlers, job_service, _ = dependencies
    result = handlers.research_salary({}, {"job_id": 7})
    assert result["context_updates"]["salary_ideal"] == 15000.0
    assert job_service.job.salary_min == 8000.0
    assert job_service.job.salary_max == 15000.0


def test_detect_application_url_preserves_full_easy_apply_url(dependencies) -> None:
    handlers, job_service, _ = dependencies
    result = handlers.detect_application_url({}, {"job_id": 7})
    assert result["status"] == "Concluída"
    assert job_service.job.application_url.endswith("?trackingId=abc")


def test_register_application_is_idempotent_and_preserves_salary_rules(
    dependencies,
) -> None:
    handlers, _, applications = dependencies
    first = handlers.register_application({}, {"job_id": 7, "curriculum_id": 5})
    second = handlers.register_application(
        {}, {"job_id": 7, "application_id": first["context_updates"]["application_id"]}
    )
    assert applications.created == 1
    assert len(applications.applications) == 1
    application = applications.applications[0]
    assert application.salary_expected == 12000.0
    assert application.salary_offered == 8000.0
    assert application.response_date is None
    assert second["context_updates"]["application_id"] == application.id


def test_cover_letter_handler_returns_new_version(dependencies) -> None:
    handlers, _, _ = dependencies
    result = handlers.generate_cover_letter({}, {"job_id": 7, "curriculum_id": 5})
    assert result["context_updates"] == {
        "cover_letter_id": 9,
        "cover_letter_version": "V1.1",
    }


def test_job_dependent_handler_rejects_missing_job(dependencies) -> None:
    handlers, _, _ = dependencies
    with pytest.raises(ValueError, match="Selecione uma vaga"):
        handlers.verify_job({}, {})


def test_manual_submission_is_not_registered_as_automation(dependencies) -> None:
    handlers, _, _ = dependencies
    assert handlers.registry().resolve("manual_submit_application") is None
