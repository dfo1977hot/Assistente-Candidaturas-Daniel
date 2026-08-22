
from pathlib import Path

SOURCE = Path(
    "acd/infrastructure/application_automation/playwright_application_browser.py"
).read_text(encoding="utf-8")


def test_gupy_resends_after_one_minute() -> None:
    assert "self.magic_link_service._timeout_seconds = 60" in SOURCE
    assert '"Reenviar link"' in SOURCE
    assert "except TimeoutError:" in SOURCE


def test_gupy_refreshes_request_timestamp_after_resend() -> None:
    assert "requested_after = datetime.now(UTC)" in SOURCE
    assert "Novo link solicitado; aguardando o novo e-mail da Gupy..." in SOURCE
