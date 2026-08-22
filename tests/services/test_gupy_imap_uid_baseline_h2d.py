from pathlib import Path

IMAP = Path(
    "acd/infrastructure/email/"
    "terra_imap_gupy_magic_link_service.py"
).read_text(encoding="utf-8")

BROWSER = Path(
    "acd/infrastructure/application_automation/"
    "playwright_application_browser.py"
).read_text(encoding="utf-8")


def test_imap_captures_sender_uid_baseline() -> None:
    assert (
        "def capture_sender_uid_baseline("
        in IMAP
    )
    assert '"search"' in IMAP
    assert '"FROM"' in IMAP
    assert "EXPECTED_SENDER" in IMAP


def test_imap_ignores_uids_at_or_before_baseline() -> None:
    assert "min_uid: int | None = None" in IMAP
    assert "numeric_id <= min_uid" in IMAP


def test_imap_fetches_by_uid() -> None:
    assert '"fetch"' in IMAP
    assert "uid_mode" in IMAP


def test_browser_captures_baseline_before_request() -> None:
    start = BROWSER.index(
        "    def _prepare_gupy("
    )
    method = BROWSER[start:]

    baseline = method.index(
        "capture_uid_baseline = getattr("
    )
    request = method.index(
        '"Receber link via e-mail"'
    )

    assert baseline < request


def test_browser_passes_uid_baseline_to_polling() -> None:
    start = BROWSER.index(
        "    def _prepare_gupy("
    )
    method = BROWSER[start:]

    assert "min_uid=uid_baseline" in method


def test_resend_refreshes_uid_baseline() -> None:
    start = BROWSER.index(
        "except TimeoutError:"
    )
    method = BROWSER[start:]

    baseline = method.index(
        "uid_baseline = capture_uid_baseline("
    )
    resend = method.index(
        "resend.first.click()"
    )

    assert baseline < resend