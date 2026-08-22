from pathlib import Path

BROWSER_PATH = Path(
    "acd/infrastructure/application_automation/"
    "playwright_application_browser.py"
)


def _source() -> str:
    return BROWSER_PATH.read_text(encoding="utf-8")


def test_gupy_uses_playwright_productive_path() -> None:
    source = _source()

    playwright_import = source.index(
        "from playwright.sync_api import sync_playwright"
    )
    gupy_prepare = source.index(
        'if platform == "Gupy":',
        playwright_import,
    )

    assert playwright_import < gupy_prepare
    assert "self._prepare_gupy(page, profile, progress)" in source


def test_gupy_never_uses_regular_password_login() -> None:
    source = _source()

    assert "_try_gupy_password_login" not in source
    assert "_fill_gupy_password_login" not in source
    assert "_configured_login_for_gupy_page" not in source
    assert "resolve_login_for_url(" not in source


def test_gupy_uses_passwordless_and_imap() -> None:
    source = _source()

    assert 'page.locator("#passwordlessSignin")' in source
    assert (
        "self._click_gupy_passwordless_entry(auth_surface, progress)"
        in source
    )
    assert "self.magic_link_service.wait_for_link(" in source
    assert "TerraImapGupyMagicLinkService" in source


def test_gupy_passwordless_email_comes_from_profile() -> None:
    source = _source()

    assert "passwordless_email = profile.email.strip()" in source
    assert 'passwordless_email = "dfo1977@terra.com.br"' not in source
