from __future__ import annotations

import pytest

from acd.infrastructure.application_automation.playwright_application_browser import (
    PlaywrightApplicationBrowser,
)


class _Context:
    def __init__(self, pages: list[object]) -> None:
        self.pages = pages


class _Page:
    def __init__(self, url: str, context: _Context | None = None) -> None:
        self.url = url
        self.context = context or _Context([self])
        self.front = False
        self.wait_calls = 0
        self.on_wait = None

    def bring_to_front(self) -> None:
        self.front = True

    def wait_for_timeout(self, _milliseconds: int) -> None:
        self.wait_calls += 1
        if self.on_wait is not None:
            self.on_wait()


def test_resolve_authenticated_gupy_page_prefers_ready_application(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    signin = _Page("https://tenant.gupy.io/candidates/signin")
    candidate = _Page("https://tenant.gupy.io/candidates/profile")
    application = _Page(
        "https://tenant.gupy.io/candidates/applications/123/steps/456/curriculum"
    )
    context = _Context([signin, candidate, application])
    for page in context.pages:
        page.context = context

    monkeypatch.setattr(
        PlaywrightApplicationBrowser,
        "_gupy_application_page_is_ready",
        classmethod(lambda cls, page: page is application),
    )
    monkeypatch.setattr(
        PlaywrightApplicationBrowser,
        "_gupy_authenticated_candidate_page",
        classmethod(lambda cls, page: page in {candidate, application}),
    )

    resolved = PlaywrightApplicationBrowser._resolve_authenticated_gupy_page(signin)

    assert resolved is application
    assert application.front is True


def test_wait_for_gupy_authenticated_page_does_not_accept_signin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    signin = _Page("https://tenant.gupy.io/candidates/signin")
    authenticated = _Page("https://tenant.gupy.io/candidates/profile")
    context = _Context([signin])
    signin.context = context
    authenticated.context = context

    monkeypatch.setattr(
        PlaywrightApplicationBrowser,
        "_gupy_application_page_is_ready",
        classmethod(lambda cls, page: False),
    )
    monkeypatch.setattr(
        PlaywrightApplicationBrowser,
        "_gupy_authenticated_candidate_page",
        classmethod(lambda cls, page: page is authenticated),
    )

    signin.on_wait = lambda: (
        context.pages.append(authenticated)
        if authenticated not in context.pages
        else None
    )

    resolved = PlaywrightApplicationBrowser._wait_for_gupy_authenticated_page(
        signin,
        timeout_ms=1_000,
    )

    assert resolved is authenticated
    assert signin.wait_calls >= 1


def test_wait_for_gupy_authenticated_page_times_out_on_signin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    signin = _Page("https://tenant.gupy.io/candidates/signin")

    monkeypatch.setattr(
        PlaywrightApplicationBrowser,
        "_gupy_application_page_is_ready",
        classmethod(lambda cls, page: False),
    )
    monkeypatch.setattr(
        PlaywrightApplicationBrowser,
        "_gupy_authenticated_candidate_page",
        classmethod(lambda cls, page: False),
    )

    with pytest.raises(RuntimeError, match="sessão autenticada não foi confirmada"):
        PlaywrightApplicationBrowser._wait_for_gupy_authenticated_page(
            signin,
            timeout_ms=400,
        )


def test_wait_for_gupy_authenticated_page_returns_existing_authenticated_tab(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    signin = _Page("https://tenant.gupy.io/candidates/signin")
    authenticated = _Page(
        "https://tenant.gupy.io/candidates/applications/123/steps/456/curriculum"
    )
    context = _Context([signin, authenticated])
    signin.context = context
    authenticated.context = context

    monkeypatch.setattr(
        PlaywrightApplicationBrowser,
        "_gupy_application_page_is_ready",
        classmethod(lambda cls, page: page is authenticated),
    )
    monkeypatch.setattr(
        PlaywrightApplicationBrowser,
        "_gupy_authenticated_candidate_page",
        classmethod(lambda cls, page: page is authenticated),
    )

    resolved = PlaywrightApplicationBrowser._wait_for_gupy_authenticated_page(
        signin,
        timeout_ms=400,
    )

    assert resolved is authenticated
    assert signin.wait_calls == 0
