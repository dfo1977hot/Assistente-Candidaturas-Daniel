from acd.application.application_orchestrator import ApplicationOrchestrator
from acd.application.start_application_use_case import (
    StartApplicationUseCase,
)


def test_execute_starts_application() -> None:
    orchestrator = ApplicationOrchestrator()

    use_case = StartApplicationUseCase(orchestrator)

    session = use_case.execute(
        company_name="OpenAI",
        job_title="Engineer",
        job_description="Description",
    )

    assert session.company_name == "OpenAI"
    assert session.job_title == "Engineer"
    assert session.job_description == "Description"