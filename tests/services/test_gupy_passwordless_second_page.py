from __future__ import annotations

from acd.infrastructure.application_automation.playwright_application_browser import (
    PlaywrightApplicationBrowser,
)


class _Locator:
    def __init__(
        self,
        *,
        visible: bool = True,
        editable: bool = True,
        count_value: int = 1,
        input_type: str = "text",
    ) -> None:
        self.visible = visible
        self.editable = editable
        self.count_value = count_value
        self.input_type = input_type
        self.values: list[str] = []

    @property
    def first(self) -> _Locator:
        return self

    def nth(self, _index: int) -> _Locator:
        return self

    def count(self) -> int:
        return self.count_value

    def is_visible(self) -> bool:
        return self.visible

    def is_editable(self) -> bool:
        return self.editable

    def fill(self, value: str) -> None:
        self.values.append(value)

    def get_attribute(self, name: str) -> str | None:
        if name == "type":
            return self.input_type
        return None


class _PasswordlessPage:
    def __init__(self) -> None:
        self.email = _Locator()
        self.confirmation = _Locator()
        self.hidden = _Locator(
            visible=False,
            editable=False,
            count_value=0,
        )
        self.password = _Locator(
            visible=False,
            editable=False,
            count_value=0,
            input_type="password",
        )
        self.url = (
            "https://empresa.gupy.io/"
            "candidates/passwordless-signin"
        )
        self.waited_url = False

    def wait_for_url(
        self,
        _pattern: object,
        **_kwargs: object,
    ) -> None:
        self.waited_url = True

    def wait_for_timeout(self, _milliseconds: int) -> None:
        return None

    def get_by_text(
        self,
        _value: object,
        **_kwargs: object,
    ) -> _Locator:
        return self.confirmation

    def get_by_label(
        self,
        value: str,
        **_kwargs: object,
    ) -> _Locator:
        if "mail" in value.casefold() or "cpf" in value.casefold():
            return self.email
        return self.hidden

    def get_by_placeholder(
        self,
        value: str,
        **_kwargs: object,
    ) -> _Locator:
        if "mail" in value.casefold() or "cpf" in value.casefold():
            return self.email
        return self.hidden

    def get_by_role(
        self,
        role: str,
        **_kwargs: object,
    ) -> _Locator:
        if role == "textbox":
            return self.email
        return self.hidden

    def locator(self, selector: str) -> _Locator:
        if selector == 'input[type="password"]':
            return self.password

        if (
            "cloudflare" in selector.casefold()
            or "turnstile" in selector.casefold()
            or "challenge" in selector.casefold()
        ):
            return self.hidden

        if selector == "input":
            return self.email

        return self.hidden


def test_waits_for_dedicated_passwordless_page_before_filling() -> None:
    page = _PasswordlessPage()

    PlaywrightApplicationBrowser._wait_for_gupy_passwordless_page(page)

    assert page.waited_url


def test_fills_blank_field_on_second_passwordless_page() -> None:
    page = _PasswordlessPage()

    filled = PlaywrightApplicationBrowser._fill_gupy_passwordless_email(
        page,
        "dfo1977@terra.com.br",
    )

    assert filled
    assert page.email.values == [
        "",
        "dfo1977@terra.com.br",
    ]


def test_confirms_link_request_before_mailbox_polling() -> None:
    page = _PasswordlessPage()

    confirmed = (
        PlaywrightApplicationBrowser
        ._wait_for_gupy_link_sent_confirmation(page)
    )

    assert confirmed
    assert page.confirmation.is_visible()
