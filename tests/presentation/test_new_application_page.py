"""Qt tests for the explicit new-application page interactions."""

from __future__ import annotations

from types import SimpleNamespace

from acd.presentation.pages.new_application_page import NewApplicationPage


class _NewApplicationViewModel:
    """Record page requests without invoking application infrastructure."""

    def __init__(self) -> None:
        self.requests: list[tuple[str, str, str]] = []
        self.clear_calls = 0

    def start_application(
        self,
        *,
        company_name: str,
        job_title: str,
        job_description: str,
    ) -> SimpleNamespace:
        self.requests.append((company_name, job_title, job_description))
        return SimpleNamespace(company_name=company_name)

    def clear(self) -> None:
        self.clear_calls += 1


def test_new_application_page_starts_application_with_entered_values(qtbot) -> None:
    view_model = _NewApplicationViewModel()
    page = NewApplicationPage(view_model=view_model)
    qtbot.addWidget(page)
    page.company_edit.setText("ACD")
    page.job_edit.setText("Python Engineer")
    page.description_edit.setPlainText("Python and SQL")

    page.start_button.click()

    assert view_model.requests == [("ACD", "Python Engineer", "Python and SQL")]
    assert page.status_label.text() == "Candidatura iniciada para ACD"


def test_new_application_page_clears_fields_and_view_model(qtbot) -> None:
    view_model = _NewApplicationViewModel()
    page = NewApplicationPage(view_model=view_model)
    qtbot.addWidget(page)
    page.company_edit.setText("ACD")
    page.job_edit.setText("Python Engineer")
    page.description_edit.setPlainText("Python and SQL")
    page.status_label.setText("Candidatura iniciada para ACD")

    page.clear_button.click()

    assert page.company_edit.text() == ""
    assert page.job_edit.text() == ""
    assert page.description_edit.toPlainText() == ""
    assert page.status_label.text() == ""
    assert view_model.clear_calls == 1
