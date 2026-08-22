from pathlib import Path

SOURCE = Path(
    "acd/infrastructure/application_automation/playwright_application_browser.py"
).read_text(encoding="utf-8")


def test_gupy_passwordless_flow_is_exclusive() -> None:
    assert "_try_gupy_password_login" not in SOURCE
    assert "_fill_gupy_password_login" not in SOURCE
    assert "resolve_login_for_url(candidate_url)" not in SOURCE


def test_gupy_prepare_returns_controlled_page() -> None:
    start = SOURCE.index("    def _prepare_gupy(")
    end = SOURCE.index(
        "    @staticmethod\n    def _resolve_gupy_candidate_page",
        start,
    )
    method = SOURCE[start:end]

    assert "self._click_gupy_passwordless_entry(auth_surface, progress)" in method
    assert "self.magic_link_service.wait_for_link(" in method
    assert "return page" in method


def test_gupy_resolver_prioritizes_passwordless() -> None:
    start = SOURCE.index("    def _resolve_gupy_candidate_page(")
    tail = SOURCE[start:]
    assert tail.index('"/candidates/passwordless-signin"') < tail.index(
        '"/candidates/signin"'
    )
