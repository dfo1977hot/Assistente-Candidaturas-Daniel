from __future__ import annotations

from pathlib import Path

from acd.infrastructure.application_automation.playwright_application_browser import (
    PlaywrightApplicationBrowser,
)


class _Locator:
    def __init__(self, *, visible: bool = False) -> None:
        self.visible = visible

    @property
    def first(self) -> _Locator:
        return self

    def count(self) -> int:
        return 1 if self.visible else 0

    def is_visible(self) -> bool:
        return self.visible


class _Page:
    def __init__(self, url: str) -> None:
        self.url = url

    def locator(self, selector: str) -> _Locator:
        visible = selector == 'form input:not([type="hidden"])'
        return _Locator(visible=visible)


def test_authenticated_application_route_is_ready() -> None:
    page = _Page(
        "https://tenant.gupy.io/candidates/applications/123/steps/456/curriculum"
    )

    assert PlaywrightApplicationBrowser._gupy_application_page_is_ready(page)


def test_public_candidate_route_is_not_ready() -> None:
    page = _Page("https://tenant.gupy.io/candidates/signin")

    assert not PlaywrightApplicationBrowser._gupy_application_page_is_ready(page)


def test_fast_stage_polling_defaults_are_bounded() -> None:
    source = Path(
        "acd/infrastructure/application_automation/"
        "playwright_application_browser.py"
    ).read_text(encoding="utf-8")

    start = source.index("def _wait_for_gupy_stage_change")
    end = source.index("def _gupy_source_label", start)
    method = source[start:end]

    assert "timeout_ms: int = 8_000" in method
    assert "interval_ms = 100" in method


def test_post_auth_navigation_uses_short_fast_path() -> None:
    source = Path(
        "acd/infrastructure/application_automation/"
        "playwright_application_browser.py"
    ).read_text(encoding="utf-8")

    start = source.index("def _open_gupy_application_after_authentication")
    end = source.index("def _gupy_human_verification_visible", start)
    method = source[start:end]

    assert "_gupy_candidate_href_from_public_job" in method
    assert "_resolve_ready_gupy_application_page" in method
    assert "_wait_for_ready_gupy_application_page" in method
    assert "controls_deadline = time.monotonic() + 8.0" in method
    assert "for _ in range(30):" not in method
    assert "page.wait_for_timeout(500)" not in method
