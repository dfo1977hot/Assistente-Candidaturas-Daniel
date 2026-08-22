from __future__ import annotations

from pathlib import Path

from acd.services.settings_service import (
    LoginCredential,
    SettingsService,
)


class _MemoryKeyring:
    def __init__(self) -> None:
        self.values: dict[tuple[str, str], str] = {}

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


def test_save_gupy_login_uses_canonical_service_name(
    tmp_path: Path,
    monkeypatch,
) -> None:
    service = _service(
        tmp_path,
        monkeypatch,
    )

    service.save_login(
        LoginCredential(
            service="gupy",
            username="daniel@example.com",
        ),
        "senha-segura",
    )

    logins = service.list_logins()

    assert len(logins) == 1
    assert logins[0].service == "Gupy"
    assert (
        logins[0].username
        == "daniel@example.com"
    )


def test_get_login_accepts_provider_id_or_display_name(
    tmp_path: Path,
    monkeypatch,
) -> None:
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

    by_id = service.get_login("gupy")
    by_name = service.get_login("Gupy")

    assert by_id is not None
    assert by_name is not None
    assert by_id.username == "daniel@example.com"
    assert by_name.username == "daniel@example.com"


def test_resolve_gupy_login_from_changing_vacancy_url(
    tmp_path: Path,
    monkeypatch,
) -> None:
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

    resolved = service.resolve_login_for_url(
        "https://empresa-exemplo.gupy.io/jobs/123456"
    )

    assert resolved is not None
    assert resolved.provider.provider_id == "gupy"
    assert resolved.provider.display_name == "Gupy"
    assert (
        resolved.credential.username
        == "daniel@example.com"
    )
    assert resolved.password == "senha-segura"


def test_different_gupy_subdomains_share_same_login(
    tmp_path: Path,
    monkeypatch,
) -> None:
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

    first = service.resolve_login_for_url(
        "https://empresa-a.gupy.io/jobs/1"
    )

    second = service.resolve_login_for_url(
        "https://empresa-b.gupy.io/jobs/999"
    )

    assert first is not None
    assert second is not None

    assert (
        first.credential.username
        == second.credential.username
    )

    assert (
        first.password
        == second.password
        == "senha-segura"
    )


def test_unknown_provider_does_not_return_gupy_login(
    tmp_path: Path,
    monkeypatch,
) -> None:
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

    assert (
        service.resolve_login_for_url(
            "https://example.com/jobs/123"
        )
        is None
    )


def test_has_login_for_gupy_url(
    tmp_path: Path,
    monkeypatch,
) -> None:
    service = _service(
        tmp_path,
        monkeypatch,
    )

    assert not service.has_login_for_url(
        "https://empresa.gupy.io/jobs/123"
    )

    service.save_login(
        LoginCredential(
            service="Gupy",
            username="daniel@example.com",
        ),
        "senha-segura",
    )

    assert service.has_login_for_url(
        "https://empresa.gupy.io/jobs/123"
    )


def test_delete_login_by_provider_id_removes_canonical_login(
    tmp_path: Path,
    monkeypatch,
) -> None:
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

    service.delete_login("gupy")

    assert service.get_login("Gupy") is None
    assert service.login_password("Gupy") == ""