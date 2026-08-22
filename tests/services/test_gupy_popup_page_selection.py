from pathlib import Path


def test_productive_gupy_flow_resolves_candidate_page_after_redirects() -> None:
    source = Path(
        "acd/infrastructure/application_automation/"
        "playwright_application_browser.py"
    ).read_text(encoding="utf-8")

    assert (
        "page = self._resolve_gupy_candidate_page(page)"
        in source
    )
    assert (
        "pages = list(context.pages)"
        in source
    )
    assert '"/candidates/signin"' in source
    assert '"/candidates/passwordless-signin"' in source
