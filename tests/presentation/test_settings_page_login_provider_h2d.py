from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from acd.presentation.pages.settings_page import SettingsPage
from acd.services.settings_service import LoginCredential, SettingsService


class _MemoryKeyring:
    def __init__(self) -> None:
        self.values: dict[
            tuple[str, str],
            str,
        ] = {}

    def get_password(
        self,
        service: str,
        account: str,
    ) -> str | None:
        return self.values.get(
            (
                service,
                account,
            )
        )

    def set_password(
        self,
        service: str,
        account: str,
        value: str,
    ) -> None:
        self.values[
            (
                service,
                account,
            )
        ] = value

    def delete_password(
        self,
        service: str,
        account: str,
    ) -> None:
        self.values.pop(
            (
                service,
                account,
            ),
            None,
        )


def _application() -> QApplication:
    return (
        QApplication.instance()
        or QApplication([])
    )


def _service(
    tmp_path: Path,
    monkeypatch,
) -> SettingsService:
    keyring = _MemoryKeyring()

    monkeypatch.setattr(
        SettingsService,
        "_keyring",
        staticmethod(
            lambda: keyring
        ),
    )

    return SettingsService(
        settings_path=(
            tmp_path
            / "settings.json"
        )
    )


def test_settings_page_offers_gupy_provider(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _application()

    service = _service(
        tmp_path,
        monkeypatch,
    )

    page = SettingsPage(service)

    assert page.login_service.isEditable()

    index = page.login_service.findText(
        "Gupy"
    )

    assert index >= 0

    assert (
        page.login_service.itemData(
            index
        )
        == "gupy"
    )

    assert (
        "Opcional"
        in page.login_url.placeholderText()
    )

    page.close()


def test_settings_page_saves_gupy_without_url(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _application()

    service = _service(
        tmp_path,
        monkeypatch,
    )

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *_args, **_kwargs: (
            QMessageBox.StandardButton.Ok
        ),
    )

    page = SettingsPage(service)

    page.login_service.setCurrentText(
        "Gupy"
    )

    page.login_username.setText(
        "daniel@example.com"
    )

    page.login_password.setText(
        "senha-segura"
    )

    assert page.login_url.text() == ""

    page._save_login()

    credential = service.get_login(
        "gupy"
    )

    assert credential is not None
    assert credential.service == "Gupy"
    assert credential.url == ""

    assert (
        credential.username
        == "daniel@example.com"
    )

    assert (
        service.login_password(
            "gupy"
        )
        == "senha-segura"
    )

    page.close()


def test_settings_page_loads_existing_gupy_login(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _application()

    service = _service(
        tmp_path,
        monkeypatch,
    )

    service.save_login(
        LoginCredential(
            service="Gupy",
            username="daniel@example.com",
        ),
        "senha-segura",
    )

    page = SettingsPage(service)

    page.login_table.selectRow(0)

    QApplication.processEvents()

    assert (
        page.login_service.currentText()
        == "Gupy"
    )

    assert (
        page.login_username.text()
        == "daniel@example.com"
    )

    assert (
        page.login_password.text()
        == "senha-segura"
    )

    page.close()