from acd.application.application_facade import ApplicationFacade


def test_start_application() -> None:
    facade = ApplicationFacade()

    session = facade.start_application(
        company_name="OpenAI",
        job_title="Engineer",
        job_description="Description",
    )

    assert session.company_name == "OpenAI"
    assert session.job_title == "Engineer"
    assert session.job_description == "Description"


def test_clear_session() -> None:
    facade = ApplicationFacade()

    facade.start_application(
        company_name="OpenAI",
        job_title="Engineer",
        job_description="Description",
    )

    facade.clear()

    assert facade.session.company_name == ""
    assert facade.session.job_title == ""
    assert facade.session.job_description == ""


def test_snapshot_reflects_session() -> None:
    facade = ApplicationFacade()

    facade.start_application(
        company_name="OpenAI",
        job_title="Engineer",
        job_description="Description",
    )

    snapshot = facade.snapshot()

    assert snapshot.company_name == "OpenAI"
    assert snapshot.job_title == "Engineer"
    assert snapshot.job_description == "Description"
    assert snapshot.is_analyzed is False
    assert snapshot.has_resume is False
    assert snapshot.is_registered is False