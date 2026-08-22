
from pathlib import Path

SOURCE = Path(
    "acd/infrastructure/application_automation/playwright_application_browser.py"
).read_text(encoding="utf-8")


def test_time_is_available_for_gupy_confirmation_wait() -> None:
    assert "import time" in SOURCE
    assert "time.monotonic()" in SOURCE
    assert "time.sleep(0.5)" in SOURCE


def test_resend_missing_button_raise_uses_explicit_cause() -> None:
    assert (
        'raise RuntimeError(\n'
        '                        "O botão Reenviar link da Gupy não foi localizado."\n'
        '                    ) from None'
    ) in SOURCE
