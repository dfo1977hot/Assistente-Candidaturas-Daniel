from pathlib import Path


def _source() -> str:
    return Path(
        "acd/infrastructure/application_automation/"
        "playwright_application_browser.py"
    ).read_text(encoding="utf-8")


def test_gupy_passwordless_uses_confirmed_element_id_first() -> None:
    source = _source()

    id_selector = '"#passwordlessSignin"'
    aria_selector = '\'button[aria-label="Entrar sem senha"]\''

    assert id_selector in source
    assert aria_selector in source
    assert source.index(id_selector) < source.index(aria_selector)


def test_gupy_passwordless_click_confirms_expected_navigation() -> None:
    source = _source()

    assert 'button.wait_for(state="visible"' in source
    assert "button.scroll_into_view_if_needed" in source
    assert "button.click(timeout=15_000)" in source
    assert "cls._confirm_gupy_passwordless_navigation(page)" in source
    assert "/candidates/passwordless-signin" in source
