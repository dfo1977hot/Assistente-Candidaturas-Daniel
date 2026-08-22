from __future__ import annotations

from datetime import UTC, datetime

from acd.infrastructure.application_automation.playwright_application_browser import (
    PlaywrightApplicationBrowser,
)
from acd.services.assisted_application_service import ApplicantProfile


class _Locator:
    def __init__(self, label: str = "") -> None:
        self.label = label
        self.clicked = False
        self.waited = False
        self.values: list[str] = []

    @property
    def first(self) -> _Locator:
        return self

    def nth(self, _index: int) -> _Locator:
        return self

    def count(self) -> int:
        return 1

    def is_visible(self) -> bool:
        return True

    def is_editable(self) -> bool:
        return True

    def is_enabled(self) -> bool:
        return True

    def click(self, **_kwargs: object) -> None:
        self.clicked = True

    def fill(self, value: str) -> None:
        self.values.append(value)

    def wait_for(self, **_kwargs: object) -> None:
        self.waited = True

    def scroll_into_view_if_needed(self, **_kwargs: object) -> None:
        return None


class _MagicLinkService:
    def __init__(self) -> None:
        self.called = False
        self.requested_after: datetime | None = None

    def wait_for_link(self, **kwargs: object) -> str:
        self.called = True
        self.requested_after = kwargs["requested_after"]  # type: ignore[assignment]
        return "https://login.gupy.io/magic?token=test"


class _Page:
    def __init__(self) -> None:
        self.url = "https://empresa.gupy.io/candidates/signin"
        self.buttons: dict[str, _Locator] = {}
        self.email = _Locator("E-mail ou CPF")
        self.confirmation = _Locator("confirmação")
        self.visited: list[str] = []

    def get_by_role(
        self,
        _role: str,
        name: str = "",
        **_kwargs: object,
    ) -> _Locator:
        if not name:
            return self.email
        return self.buttons.setdefault(name, _Locator(name))

    def get_by_text(
        self,
        value: object,
        **_kwargs: object,
    ) -> _Locator:
        if isinstance(value, str) and "Entrar sem senha" in value:
            return _Locator(value)
        return self.confirmation

    def get_by_label(
        self,
        _value: str,
        **_kwargs: object,
    ) -> _Locator:
        return self.email

    def get_by_placeholder(
        self,
        _value: str,
        **_kwargs: object,
    ) -> _Locator:
        return self.email

    def locator(self, selector: str) -> _Locator:
        if selector == "#passwordlessSignin":
            return self.buttons.setdefault(
                "Entrar sem senha",
                _Locator("Entrar sem senha"),
            )
        return self.email

    def wait_for_url(
        self,
        _pattern: object,
        **_kwargs: object,
    ) -> None:
        if "passwordless" in str(_pattern):
            self.url = (
                "https://empresa.gupy.io/"
                "candidates/passwordless-signin"
            )

    def wait_for_timeout(self, _milliseconds: int) -> None:
        return None

    def goto(self, url: str, **_kwargs: object) -> None:
        self.visited.append(url)
        self.url = url


class _Browser(PlaywrightApplicationBrowser):
    @classmethod
    def _return_to_gupy_application(
        cls,
        page: object,
        _application_url: str,
    ) -> object:
        return page

    @classmethod
    def _wait_for_gupy_authenticated_page(
        cls,
        page: object,
        *,
        timeout_ms: int = 20_000,
    ) -> object:
        del timeout_ms
        return page

    @staticmethod
    def _dismiss_common_banners(_page: object) -> None:
        return None

    @staticmethod
    def _wait_for_gupy_passwordless_page(_page: object) -> None:
        return None

    @staticmethod
    def _wait_for_gupy_link_sent_confirmation(_page: object) -> bool:
        return True

    @staticmethod
    def _fill_gupy_passwordless_email(
        _page: object,
        _email_address: str,
    ) -> bool:
        return True


def test_waits_for_email_delivery_choice() -> None:
    page = _Page()

    PlaywrightApplicationBrowser._wait_for_gupy_delivery_method_page(page)

    assert page.buttons["Receber link via e-mail"].waited


def test_gupy_clicks_receive_link_by_email_before_polling_imap() -> None:
    magic_link_service = _MagicLinkService()
    browser = _Browser(
        magic_link_service=magic_link_service,
    )  # type: ignore[arg-type]

    page = _Page()
    progress_events: list[object] = []

    browser._prepare_gupy(
        page,
        ApplicantProfile(
            "Daniel",
            "dfo1977@terra.com.br",
        ),
        progress_events.append,
    )

    assert page.buttons["Entrar sem senha"].clicked
    assert page.buttons["Continuar"].clicked
    assert page.buttons["Receber link via e-mail"].clicked
    assert magic_link_service.called
    assert magic_link_service.requested_after is not None
    assert magic_link_service.requested_after.tzinfo is UTC
    assert page.visited == [
        "https://login.gupy.io/magic?token=test",
    ]
