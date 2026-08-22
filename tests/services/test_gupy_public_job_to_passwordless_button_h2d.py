from pathlib import Path

SOURCE = Path(
    "acd/infrastructure/application_automation/playwright_application_browser.py"
).read_text(encoding="utf-8")


def test_public_gupy_job_moves_to_signin_before_resolving_candidate_page() -> None:
    start = SOURCE.index("    def _prepare_gupy(")
    method = SOURCE[start:]

    assert 'if current_path.startswith("/jobs/"):' in method
    assert '"/candidates/signin"' in method
    assert 'self._click_gupy_passwordless_entry(auth_surface, progress)' in method


def test_gupy_passwordless_click_uses_exact_live_dom_id() -> None:
    start = SOURCE.index("    def _click_gupy_passwordless_entry(")
    method = SOURCE[start:]

    assert 'page.locator("#passwordlessSignin")' in method
    assert "/candidates/passwordless-signin" in method


def test_regular_password_login_path_does_not_exist() -> None:
    assert "_try_gupy_password_login" not in SOURCE
    assert "_fill_gupy_password_login" not in SOURCE
    assert "_configured_login_for_gupy_page" not in SOURCE
