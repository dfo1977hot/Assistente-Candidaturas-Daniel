from acd.presentation.pages.application_wizard import (
    CompanyStep,
)


def test_company_step_emits_signal(
    qtbot,
):
    widget = CompanyStep()

    qtbot.addWidget(widget)

    values = []

    widget.completed.connect(values.append)

    widget.company_edit.setText("OpenAI")

    widget.next_button.click()

    assert values == ["OpenAI"]