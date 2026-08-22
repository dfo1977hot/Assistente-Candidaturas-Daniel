from pathlib import Path

SOURCE = Path("acd/infrastructure/application_automation/playwright_application_browser.py").read_text(encoding="utf-8")


def test_gupy_confirmation_returns_boolean() -> None:
    start = SOURCE.index("    def _wait_for_gupy_link_sent_confirmation(")
    tail = SOURCE[start:start + 2500]
    assert "-> bool:" in tail
    assert "return True" in tail
    assert "return False" in tail


def test_prepare_gupy_can_continue_to_outlook() -> None:
    assert "if not self._wait_for_gupy_link_sent_confirmation(" in SOURCE
    assert "self.magic_link_service.wait_for_link(" in SOURCE
