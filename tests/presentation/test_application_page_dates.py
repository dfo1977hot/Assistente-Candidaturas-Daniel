from __future__ import annotations

from PySide6.QtCore import QDate

from acd.presentation.pages.application_page import ApplicationPage


def test_new_application_uses_current_date_and_blank_optional_dates(qtbot) -> None:
    page = ApplicationPage()
    qtbot.addWidget(page)

    assert page.application_date_input.date() == QDate.currentDate()
    assert page.next_follow_up_input.text().strip() == ""
    assert page.response_date_input.text().strip() == ""
    assert page.interview_date_input.text().strip() == ""
    assert page.interview_date_input.isReadOnly() is True


def test_clear_form_restores_current_date_and_blank_optional_dates(qtbot) -> None:
    page = ApplicationPage()
    qtbot.addWidget(page)

    page.application_date_input.setDate(QDate(2026, 1, 15))
    page.next_follow_up_input.setDate(QDate(2026, 1, 16))
    page.response_date_input.setDate(QDate(2026, 1, 17))
    page.interview_date_input.setDate(QDate(2026, 1, 18))

    page._clear_form()

    assert page.application_date_input.date() == QDate.currentDate()
    assert page.next_follow_up_input.text().strip() == ""
    assert page.response_date_input.text().strip() == ""
    assert page.interview_date_input.text().strip() == ""
