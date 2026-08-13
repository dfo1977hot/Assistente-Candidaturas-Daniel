"""Preferências locais e cofre de credenciais do ACD."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from acd.security.secret_provider import EnvironmentSecretProvider, read_setting


@dataclass(slots=True)
class LoginCredential:
    """Metadados de um login; a senha permanece no cofre do sistema operacional."""

    service: str
    url: str = ""
    username: str = ""
    notes: str = ""


class SettingsService:
    """Persiste preferências e usa keyring para armazenar segredos."""

    APP_KEYRING_SERVICE = "ACD - Assistente de Candidaturas"
    OPENAI_KEY = "api:openai"
    GOOGLE_KEY = "api:google"

    def __init__(self, settings_path: Path | None = None) -> None:
        default_path = Path.home() / ".acd" / "settings.json"
        self._settings_path = settings_path or default_path
        self._settings_path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    @property
    def settings_path(self) -> Path:
        return self._settings_path

    def startup_mode(self) -> str:
        value = str(self._data.get("startup_mode", "maximized")).lower()
        return value if value in {"maximized", "minimized"} else "maximized"

    def set_startup_mode(self, mode: str) -> None:
        normalized = mode.strip().lower()
        if normalized not in {"maximized", "minimized"}:
            raise ValueError("Modo de inicialização inválido.")
        self._data["startup_mode"] = normalized
        self._save()

    def browser_headless(self) -> bool:
        """Return whether LinkedIn browser automations should run headless."""
        return bool(self._data.get("browser_headless", False))

    def set_browser_headless(self, enabled: bool) -> None:
        self._data["browser_headless"] = bool(enabled)
        self._save()

    def get_api_key(self, provider: str) -> str:
        provider = provider.strip().lower()
        account = self._api_account(provider)
        secret = self._get_secret(account)
        if secret:
            return secret
        if provider == "openai":
            return EnvironmentSecretProvider().get_secret("OPENAI_API_KEY") or ""
        if provider == "google":
            return read_setting("GOOGLE_PLACES_API_KEY")
        return ""

    def set_api_key(self, provider: str, api_key: str) -> None:
        account = self._api_account(provider.strip().lower())
        value = api_key.strip()
        if not value:
            self._delete_secret(account)
            return
        self._set_secret(account, value)

    def delete_api_key(self, provider: str) -> None:
        self._delete_secret(self._api_account(provider.strip().lower()))

    def test_openai_key(self, api_key: str | None = None) -> tuple[bool, str]:
        key = (api_key or self.get_api_key("openai")).strip()
        if not key:
            return False, "Chave da OpenAI não configurada."
        try:
            from openai import AuthenticationError, OpenAI
        except ImportError:
            return False, "A biblioteca openai não está instalada."
        try:
            OpenAI(api_key=key).models.list()
        except AuthenticationError:
            return False, "Chave da OpenAI inválida ou sem autenticação."
        except Exception as exc:  # conexão, proxy, indisponibilidade etc.
            return False, f"Não foi possível validar a chave: {exc}"
        return True, "Chave da OpenAI válida."

    def list_logins(self) -> list[LoginCredential]:
        rows = self._data.get("logins", [])
        result: list[LoginCredential] = []
        for row in rows if isinstance(rows, list) else []:
            if not isinstance(row, dict) or not str(row.get("service", "")).strip():
                continue
            result.append(
                LoginCredential(
                    service=str(row.get("service", "")).strip(),
                    url=str(row.get("url", "")).strip(),
                    username=str(row.get("username", "")).strip(),
                    notes=str(row.get("notes", "")).strip(),
                )
            )
        return result

    def save_login(self, credential: LoginCredential, password: str | None = None) -> None:
        service = credential.service.strip()
        if not service:
            raise ValueError("Informe o nome do serviço.")
        normalized = LoginCredential(
            service=service,
            url=credential.url.strip(),
            username=credential.username.strip(),
            notes=credential.notes.strip(),
        )
        rows = [item for item in self.list_logins() if item.service.casefold() != service.casefold()]
        rows.append(normalized)
        rows.sort(key=lambda item: item.service.casefold())
        self._data["logins"] = [asdict(item) for item in rows]
        self._save()
        if password is not None:
            if password:
                self._set_secret(self._login_account(service), password)
            else:
                self._delete_secret(self._login_account(service))

    def login_password(self, service: str) -> str:
        return self._get_secret(self._login_account(service.strip()))

    def delete_login(self, service: str) -> None:
        target = service.strip().casefold()
        rows = [item for item in self.list_logins() if item.service.casefold() != target]
        self._data["logins"] = [asdict(item) for item in rows]
        self._save()
        self._delete_secret(self._login_account(service.strip()))

    def diagnostic_snapshot(self) -> dict[str, str]:
        return {
            "Arquivo de configurações": str(self._settings_path),
            "Inicialização": "Maximizado" if self.startup_mode() == "maximized" else "Minimizado",
            "Navegador LinkedIn": "Segundo plano" if self.browser_headless() else "Visível",
            "OpenAI": "Configurada" if self.get_api_key("openai") else "Não configurada",
            "Google": "Configurada" if self.get_api_key("google") else "Não configurada",
            "Logins cadastrados": str(len(self.list_logins())),
        }

    def _load(self) -> dict[str, Any]:
        if not self._settings_path.exists():
            return {}
        try:
            value = json.loads(self._settings_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return value if isinstance(value, dict) else {}

    def _save(self) -> None:
        temporary = self._settings_path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(self._settings_path)

    @staticmethod
    def _api_account(provider: str) -> str:
        accounts = {"openai": SettingsService.OPENAI_KEY, "google": SettingsService.GOOGLE_KEY}
        try:
            return accounts[provider]
        except KeyError as exc:
            raise ValueError(f"Provedor de API não suportado: {provider}") from exc

    @staticmethod
    def _login_account(service: str) -> str:
        return f"login:{service.casefold()}"

    def _get_secret(self, account: str) -> str:
        keyring = self._keyring()
        return keyring.get_password(self.APP_KEYRING_SERVICE, account) or ""

    def _set_secret(self, account: str, value: str) -> None:
        keyring = self._keyring()
        keyring.set_password(self.APP_KEYRING_SERVICE, account, value)

    def _delete_secret(self, account: str) -> None:
        keyring = self._keyring()
        try:
            keyring.delete_password(self.APP_KEYRING_SERVICE, account)
        except Exception:
            # keyring pode sinalizar ausência do item; apagar um segredo inexistente é idempotente.
            return

    @staticmethod
    def _keyring():
        try:
            import keyring
        except ImportError as exc:
            raise RuntimeError(
                "O pacote keyring não está instalado. Instale as dependências do projeto."
            ) from exc
        return keyring
