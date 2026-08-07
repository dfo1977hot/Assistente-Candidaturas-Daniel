from acd.application.application_orchestrator import ApplicationOrchestrator


def test_start_new_application_populates_session() -> None:
    orchestrator = ApplicationOrchestrator()

    session = orchestrator.start_new_application(
        company_name="OpenAI",
        job_title="Software Engineer",
        job_description="Develop AI systems.",
    )

    assert session.company_name == "OpenAI"
    assert session.job_title == "Software Engineer"
    assert session.job_description == "Develop AI systems."
    assert session.has_job_description is True


def test_clear_resets_session() -> None:
    orchestrator = ApplicationOrchestrator()

    orchestrator.start_new_application(
        company_name="OpenAI",
        job_title="Software Engineer",
        job_description="Develop AI systems.",
    )

    orchestrator.clear()

    session = orchestrator.session

    assert session.company_name == ""
    assert session.job_title == ""
    assert session.job_description == ""
    assert session.has_job_description is False
    assert session.is_analyzed is False
    assert session.has_resume is False
    assert session.is_registered is False


def test_session_instance_is_reused() -> None:
    orchestrator = ApplicationOrchestrator()

    session_1 = orchestrator.session

    session_2 = orchestrator.start_new_application(
        company_name="Company",
        job_title="Role",
        job_description="Description",
    )

    assert session_1 is session_2


def test_services_are_stored() -> None:
    company = object()
    job = object()
    application = object()
    analysis = object()

    orchestrator = ApplicationOrchestrator(
        company_service=company,
        job_service=job,
        application_service=application,
        job_analysis_service=analysis,
    )

    assert orchestrator.company_service is company
    assert orchestrator.job_service is job
    assert orchestrator.application_service is application
    assert orchestrator.job_analysis_service is analysis