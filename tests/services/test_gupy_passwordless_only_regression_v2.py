from pathlib import Path

SOURCE = Path(
    "acd/infrastructure/application_automation/playwright_application_browser.py"
).read_text(encoding="utf-8")


def test_gupy_has_no_username_password_login_code() -> None:
    assert "_try_gupy_password_login" not in SOURCE
    assert "_configured_login_for_gupy_page" not in SOURCE
    assert "_fill_gupy_password_login" not in SOURCE
    assert "ResolvedLoginCredential" not in SOURCE
    assert "Usando o login Gupy salvo" not in SOURCE


def test_productive_gupy_flow_starts_with_passwordless() -> None:
    start = SOURCE.index("    def _prepare_gupy(")
    method = SOURCE[start:]

    assert "self._clear_gupy_signin_credentials(auth_surface)" in method
    assert "self._click_gupy_passwordless_entry(auth_surface, progress)" in method
    assert "passwordless_email = profile.email.strip()" in method
    assert "self.magic_link_service.wait_for_link(" in method
    assert "page.goto(" in method
    assert "magic_link" in method
