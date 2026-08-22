from __future__ import annotations

from acd.infrastructure.application_automation.playwright_application_browser import (
    GupyApplicationStage,
    PlaywrightApplicationBrowser,
)


class _Locator:
    def __init__(
        self,
        *,
        text: str = "",
        visible: bool = True,
        on_click: object | None = None,
    ) -> None:
        self.text = text
        self.visible = visible
        self.clicked = False
        self._on_click = on_click

    @property
    def first(self) -> _Locator:
        return self

    def count(self) -> int:
        return 1 if self.visible else 0

    def is_visible(self) -> bool:
        return self.visible

    def inner_text(self) -> str:
        return self.text

    def scroll_into_view_if_needed(self, **_kwargs: object) -> None:
        return None

    def click(self, **_kwargs: object) -> None:
        self.clicked = True
        if callable(self._on_click):
            self._on_click()


class _Page:
    def __init__(self, text: str, url: str = "https://tenant.gupy.io/candidates/applications/1/steps/2") -> None:
        self.url = url
        self.body = _Locator(text=text)
        self.buttons: dict[str, _Locator] = {}

    def locator(self, selector: str) -> _Locator:
        if selector == "body":
            return self.body
        return _Locator(visible=False)

    def get_by_role(
        self,
        role: str,
        *,
        name: str,
        exact: bool,
    ) -> _Locator:
        assert role == "button"
        assert exact is True
        return self.buttons.get(name, _Locator(visible=False))

    def wait_for_timeout(self, _milliseconds: int) -> None:
        return None


def test_detects_authenticated_welcome_stage() -> None:
    page = _Page("Olá Daniel, vamos continuar sua candidatura?")

    assert (
        PlaywrightApplicationBrowser._gupy_application_stage(page)
        is GupyApplicationStage.WELCOME
    )


def test_detects_additional_data_stage() -> None:
    page = _Page("Dados adicionais\nPreencha as informações solicitadas")

    assert (
        PlaywrightApplicationBrowser._gupy_application_stage(page)
        is GupyApplicationStage.ADDITIONAL_DATA
    )


def test_detects_company_questions_stage() -> None:
    page = _Page("Perguntas criadas pela empresa")

    assert (
        PlaywrightApplicationBrowser._gupy_application_stage(page)
        is GupyApplicationStage.COMPANY_QUESTIONS
    )


def test_detects_presentation_stage() -> None:
    page = _Page(
        "Apresente-se!\nA empresa deseja saber mais sobre você"
    )

    assert (
        PlaywrightApplicationBrowser._gupy_application_stage(page)
        is GupyApplicationStage.PRESENTATION
    )


def test_final_submission_barrier_has_precedence() -> None:
    page = _Page(
        "Apresente-se!\nFinalizar candidatura"
    )

    assert (
        PlaywrightApplicationBrowser._gupy_application_stage(page)
        is GupyApplicationStage.FINAL_SUBMISSION
    )


def test_optional_update_modal_uses_only_decline_button() -> None:
    page = _Page("Novidades")
    decline = _Locator()
    page.buttons["NÃO, OBRIGADO"] = decline

    dismissed = (
        PlaywrightApplicationBrowser
        ._dismiss_gupy_optional_update_modal(page)
    )

    assert dismissed
    assert decline.clicked


def test_welcome_continue_advances_to_additional_data() -> None:
    page = _Page("Olá Daniel, vamos continuar sua candidatura?")

    def _advance() -> None:
        page.body.text = "Dados adicionais"

    continue_button = _Locator(on_click=_advance)
    page.buttons["Continuar"] = continue_button

    progress: list[object] = []

    returned = PlaywrightApplicationBrowser._prepare_gupy_post_auth(
        page,
        progress.append,
    )

    assert returned is page
    assert continue_button.clicked
    assert (
        PlaywrightApplicationBrowser._gupy_application_stage(page)
        is GupyApplicationStage.ADDITIONAL_DATA
    )
    assert any(
        "Dados adicionais" in str(event)
        for event in progress
    )


def test_final_submission_is_never_clicked() -> None:
    page = _Page("Finalizar candidatura")
    final_button = _Locator()
    page.buttons["Finalizar candidatura"] = final_button

    progress: list[object] = []

    returned = PlaywrightApplicationBrowser._prepare_gupy_post_auth(
        page,
        progress.append,
    )

    assert returned is page
    assert not final_button.clicked
    assert any(
        "envio permanece manual" in str(event)
        for event in progress
    )
