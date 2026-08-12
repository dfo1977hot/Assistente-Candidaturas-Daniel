from acd.infrastructure.linkedin.linkedin_saved_jobs_browser import (
    LinkedInSavedJobsBrowser,
)


class Body:
    def __init__(self, text: str) -> None:
        self._text = text

    def inner_text(self, **_kwargs) -> str:
        return self._text


class Page:
    def __init__(self, text: str) -> None:
        self._text = text

    def locator(self, selector: str) -> Body:
        assert selector == "body"
        return Body(self._text)


def test_detects_portuguese_closed_application_message() -> None:
    page = Page("Esta vaga não aceita mais candidaturas.")

    assert LinkedInSavedJobsBrowser._page_reports_closed_applications(page)


def test_keeps_open_job_when_closed_message_is_absent() -> None:
    page = Page("Candidate-se agora para esta vaga.")

    assert not LinkedInSavedJobsBrowser._page_reports_closed_applications(page)


def test_extracts_linkedin_work_model_and_employment_type() -> None:
    text = "Modelo de trabalho: Híbrido. Tipo de emprego: Tempo integral."

    assert LinkedInSavedJobsBrowser._extract_work_model(text) == "Híbrido"
    assert LinkedInSavedJobsBrowser._extract_employment_type(text) == "CLT"


def test_extracts_brazilian_salary_range() -> None:
    minimum, maximum, currency = LinkedInSavedJobsBrowser._extract_salary(
        "Faixa salarial: R$ 7.500,00 a R$ 9.800,00 por mês."
    )

    assert str(minimum) == "7500.00"
    assert str(maximum) == "9800.00"
    assert currency == "BRL"
