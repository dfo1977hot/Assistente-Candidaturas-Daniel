from acd.application.application_draft import ApplicationDraft


def test_application_draft_defaults() -> None:
    draft = ApplicationDraft()

    assert draft.company_name == ""
    assert draft.job_title == ""
    assert draft.job_description == ""


def test_application_draft_clear() -> None:
    draft = ApplicationDraft(
        company_name="OpenAI",
        job_title="Engineer",
        job_description="Description",
    )

    draft.clear()

    assert draft.company_name == ""
    assert draft.job_title == ""
    assert draft.job_description == ""