from pathlib import Path

SOURCE = Path(
    "acd/infrastructure/application_automation/"
    "playwright_application_browser.py"
).read_text(encoding="utf-8")


def test_gupy_passwordless_continue_supports_submit_variants() -> None:
    start = SOURCE.index("    def _click_gupy_passwordless_continue(")
    method = SOURCE[start:]

    assert '"Continuar"' in method
    assert '"Enviar link"' in method
    assert 'button[type="submit"]' in method
    assert 'input[type="submit"]' in method


def test_productive_gupy_flow_uses_passwordless_continue() -> None:
    start = SOURCE.index("    def _prepare_gupy(")
    method = SOURCE[start:]

    assert "self._click_gupy_passwordless_continue(auth_surface)" in method
    assert "self.magic_link_service.wait_for_link(" in method
