from __future__ import annotations

from acd.infrastructure.application_automation.playwright_application_browser import (
    PlaywrightApplicationBrowser,
)


class _Locator:
    def __init__(self, *, visible: bool = True, editable: bool = True) -> None:
        self.visible = visible
        self.editable = editable
        self.values: list[str] = []
        self.waited = False

    @property
    def first(self) -> _Locator:
        return self

    def count(self) -> int:
        return 1

    def is_visible(self) -> bool:
        return self.visible

    def is_editable(self) -> bool:
        return self.editable

    def fill(self, value: str) -> None:
        self.values.append(value)

    def wait_for(self, **_kwargs: object) -> None:
        self.waited = True


class _PasswordlessPage:
    def __init__(self) -> None:
        self.email = _Locator()
        self.heading = _Locator()
        self.confirmation = _Locator()
        self.url = "https://empresa.gupy.io/candidates/passwordless-signin"
        self.waited_url = False

    def wait_for_url(self, _pattern: object, **_kwargs: object) -> None:
        self.waited_url = True

    def get_by_text(self, value: object, **_kwargs: object) -> _Locator:
        if isinstance(value, str) and "Entrar sem senha" in value:
            return self.heading
        return self.confirmation

    def get_by_label(self, value: str, **_kwargs: object) -> _Locator:
        if "E-mail ou CPF" in value:
            return self.email
        return _Locator(visible=False)

    def get_by_placeholder(self, value: str, **_kwargs: object) -> _Locator:
        if "E-mail ou CPF" in value:
            return self.email
        return _Locator(visible=False)

    def locator(self, _selector: str) -> _Locator:
        return self.email


def test_waits_for_dedicated_passwordless_page_before_filling() -> None:
    page = _PasswordlessPage()

    PlaywrightApplicationBrowser._wait_for_gupy_passwordless_page(page)

    assert page.waited_url
    assert page.heading.waited


def test_fills_blank_field_on_second_passwordless_page() -> None:
    page = _PasswordlessPage()

    filled = PlaywrightApplicationBrowser._fill_gupy_passwordless_email(
        page,
        "dfo1977@terra.com.br",
    )

    assert filled
    assert page.email.values == ["", "dfo1977@terra.com.br"]


def test_confirms_link_request_before_mailbox_polling() -> None:
    page = _PasswordlessPage()

    assert PlaywrightApplicationBrowser._wait_for_gupy_link_sent_confirmation(page)
    assert page.confirmation.waited
