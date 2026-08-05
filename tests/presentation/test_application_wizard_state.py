from acd.presentation.models.application_wizard_state import (
    ApplicationWizardState,
)


def test_default_state() -> None:
    state = ApplicationWizardState()

    assert state.company_name == ""
    assert state.job_title == ""
    assert state.job_description == ""

    assert state.analysis_result is None
    assert state.selected_resume is None
    assert state.generated_resume is None
    assert state.generated_cover_letter is None
    assert state.metadata == {}


def test_clear_state() -> None:
    state = ApplicationWizardState()

    state.company_name = "OpenAI"
    state.job_title = "Engineer"
    state.job_description = "Description"

    state.analysis_result = object()
    state.selected_resume = "resume.docx"
    state.generated_resume = "generated.docx"
    state.generated_cover_letter = "letter.docx"

    state.metadata["score"] = 92

    state.clear()

    assert state.company_name == ""
    assert state.job_title == ""
    assert state.job_description == ""

    assert state.analysis_result is None
    assert state.selected_resume is None
    assert state.generated_resume is None
    assert state.generated_cover_letter is None
    assert state.metadata == {}