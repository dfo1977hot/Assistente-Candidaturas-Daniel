from pathlib import Path

SOURCE = Path(
    "acd/infrastructure/application_automation/playwright_application_browser.py"
).read_text(encoding="utf-8")


def test_gupy_never_submits_saved_username_password() -> None:
    assert "_try_gupy_password_login" not in SOURCE
    assert "_fill_gupy_password_login" not in SOURCE
    assert "resolve_login_for_url(" not in SOURCE


def test_gupy_clears_browser_autofill_before_passwordless() -> None:
    assert "def _clear_gupy_signin_credentials(" in SOURCE
    assert "candidate.fill(\"\")" in SOURCE
    assert "self._click_gupy_passwordless_entry(auth_surface, progress)" in SOURCE


def test_gupy_human_verification_remains_manual() -> None:
    assert "def _wait_for_gupy_human_verification(" in SOURCE
    assert "_gupy_human_verification_visible(page)" in SOURCE
    assert "_wait_for_gupy_human_verification(page)" in SOURCE

def test_passwordless_navigation_does_not_accept_original_signin_button() -> None:
    start = SOURCE.index("def _confirm_gupy_passwordless_navigation")
    end = SOURCE.index("def _wait_for_gupy_passwordless_page", start)
    method = SOURCE[start:end]

    assert 'get_by_text("Entrar sem senha"' not in method
    assert "A Gupy permaneceu na tela de login com senha." in method
