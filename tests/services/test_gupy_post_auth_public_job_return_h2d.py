from __future__ import annotations

from acd.infrastructure.application_automation.playwright_application_browser import (
    PlaywrightApplicationBrowser,
)


class _Locator:
    def __init__(self, hrefs: list[str]) -> None:
        self._hrefs = hrefs

    @property
    def first(self) -> _Locator:
        return self

    def nth(self, index: int) -> _Anchor:
        return _Anchor(self._hrefs[index])

    def count(self) -> int:
        return len(self._hrefs)


class _Anchor:
    def __init__(self, href: str) -> None:
        self._href = href

    def get_attribute(self, name: str) -> str | None:
        return self._href if name == "href" else None


class _Context:
    def __init__(self, pages: list[object]) -> None:
        self.pages = pages


class _Page:
    def __init__(self, url: str) -> None:
        self.url = url
        self.context = _Context([self])
        self.front = False

    def bring_to_front(self) -> None:
        self.front = True

    def locator(self, selector: str) -> _Locator:
        assert selector == "a[href]"
        return _Locator(
            [
                "/jobs/11831230",
                "/candidates/jobs/11831230/apply",
            ]
        )


def test_gupy_candidate_apply_url_from_public_job() -> None:
    assert (
        PlaywrightApplicationBrowser._gupy_candidate_apply_url(
            "https://renner.gupy.io/jobs/11831230?jobBoardSource=linkedin"
        )
        == "https://renner.gupy.io/candidates/jobs/11831230/apply"
    )


def test_gupy_candidate_apply_url_rejects_non_public_job() -> None:
    assert (
        PlaywrightApplicationBrowser._gupy_candidate_apply_url(
            "https://renner.gupy.io/candidates/signin"
        )
        == ""
    )


def test_gupy_candidate_href_is_found_on_public_job() -> None:
    page = _Page(
        "https://renner.gupy.io/jobs/11831230?jobBoardSource=linkedin"
    )

    result = (
        PlaywrightApplicationBrowser._gupy_candidate_href_from_public_job(
            page
        )
    )

    assert (
        result
        == "https://renner.gupy.io/candidates/jobs/11831230/apply"
    )


def test_ready_application_tab_is_preferred(
    monkeypatch,
) -> None:
    public = _Page("https://renner.gupy.io/jobs/11831230")
    ready = _Page(
        "https://renner.gupy.io/candidates/applications/123/steps/456"
    )
    context = _Context([public, ready])
    public.context = context
    ready.context = context

    monkeypatch.setattr(
        PlaywrightApplicationBrowser,
        "_gupy_application_page_is_ready",
        staticmethod(lambda page: page is ready),
    )

    result = (
        PlaywrightApplicationBrowser._resolve_ready_gupy_application_page(
            public
        )
    )

    assert result is ready
    assert ready.front is True
