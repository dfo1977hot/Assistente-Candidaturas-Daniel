"""PreferÃªncias locais e cofre de credenciais do ACD."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import logging
from pathlib import Path
import re
from typing import Any

from acd.security.secret_provider import EnvironmentSecretProvider, read_setting
from acd.services.login_provider_registry import (
    LoginProvider,
    LoginProviderRegistry,
)


@dataclass(slots=True)
class LoginCredential:
    """Metadados de um login; a senha permanece no cofre do sistema operacional."""

    service: str
    url: str = ""
    username: str = ""
    notes: str = ""
    server: str = ""
    port: int = 0
    security: str = ""
    folder: str = ""
    timeout_seconds: int = 60


@dataclass(frozen=True, slots=True)
class ResolvedLoginCredential:
    """Credencial resolvida para um provedor de autenticaÃ§Ã£o."""

    provider: LoginProvider
    credential: LoginCredential
    password: str


class SettingsService:
    """Persiste preferÃªncias e usa keyring para armazenar segredos."""

    APP_KEYRING_SERVICE = "ACD - Assistente de Candidaturas"
    OPENAI_KEY = "api:openai"
    GEMINI_KEY = "api:gemini"
    GOOGLE_KEY = "api:google"

    def __init__(
        self,
        settings_path: Path | None = None,
        *,
        login_provider_registry: LoginProviderRegistry | None = None,
    ) -> None:
        default_path = Path.home() / ".acd" / "settings.json"
        self._settings_path = settings_path or default_path
        self._settings_path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()
        self._login_provider_registry = (
            login_provider_registry or LoginProviderRegistry()
        )

    @property
    def settings_path(self) -> Path:
        return self._settings_path

    @property
    def login_provider_registry(self) -> LoginProviderRegistry:
        return self._login_provider_registry

    def startup_mode(self) -> str:
        value = str(
            self._data.get(
                "startup_mode",
                "maximized",
            )
        ).lower()

        return (
            value
            if value in {"maximized", "minimized"}
            else "maximized"
        )

    def set_startup_mode(self, mode: str) -> None:
        normalized = mode.strip().lower()

        if normalized not in {
            "maximized",
            "minimized",
        }:
            raise ValueError(
                "Modo de inicializaÃ§Ã£o invÃ¡lido."
            )

        self._data["startup_mode"] = normalized
        self._save()

    def browser_headless(self) -> bool:
        """Return whether LinkedIn browser automations should run headless."""
        return bool(
            self._data.get(
                "browser_headless",
                False,
            )
        )

    def set_browser_headless(
        self,
        enabled: bool,
    ) -> None:
        self._data["browser_headless"] = bool(enabled)
        self._save()

    def ai_provider_order(self) -> tuple[str, ...]:
        raw = self._data.get(
            "ai_provider_order",
            ["ollama", "gemini", "openai"],
        )
        if not isinstance(raw, list):
            raw = ["ollama", "gemini", "openai"]

        allowed = {"ollama", "gemini", "openai"}
        normalized = tuple(
            str(item).strip().lower()
            for item in raw
            if str(item).strip().lower() in allowed
        )
        return normalized or ("ollama", "gemini", "openai")

    def set_ai_provider_order(
        self,
        providers: tuple[str, ...] | list[str],
    ) -> None:
        allowed = {"ollama", "gemini", "openai"}
        normalized: list[str] = []

        for provider in providers:
            value = str(provider).strip().lower()
            if value not in allowed:
                raise ValueError(
                    f"Provedor de IA não suportado: {provider}"
                )
            if value not in normalized:
                normalized.append(value)

        if not normalized:
            raise ValueError(
                "Configure ao menos um provedor de IA."
            )

        self._data["ai_provider_order"] = normalized
        self._save()

    def ai_model(
        self,
        provider: str,
    ) -> str:
        normalized = provider.strip().lower()
        defaults = {
            "ollama": "qwen3:8b",
            "gemini": "gemini-3.6-flash",
            "openai": "gpt-5-mini",
        }
        if normalized not in defaults:
            raise ValueError(
                f"Provedor de IA não suportado: {provider}"
            )

        models = self._data.get("ai_models", {})
        if not isinstance(models, dict):
            models = {}

        value = str(
            models.get(normalized, defaults[normalized])
        ).strip()
        return value or defaults[normalized]

    def set_ai_model(
        self,
        provider: str,
        model: str,
    ) -> None:
        normalized = provider.strip().lower()
        if normalized not in {"ollama", "gemini", "openai"}:
            raise ValueError(
                f"Provedor de IA não suportado: {provider}"
            )

        value = model.strip()
        if not value:
            raise ValueError(
                "Informe o modelo de IA."
            )

        models = self._data.get("ai_models", {})
        if not isinstance(models, dict):
            models = {}
        models = dict(models)
        models[normalized] = value
        self._data["ai_models"] = models
        self._save()

    def ollama_base_url(self) -> str:
        value = str(
            self._data.get(
                "ollama_base_url",
                "http://localhost:11434",
            )
        ).strip()
        return value or "http://localhost:11434"

    def set_ollama_base_url(
        self,
        base_url: str,
    ) -> None:
        value = base_url.strip().rstrip("/")
        if not value.startswith(("http://", "https://")):
            raise ValueError(
                "Informe uma URL válida para o Ollama."
            )
        self._data["ollama_base_url"] = value
        self._save()

    def get_api_key(
        self,
        provider: str,
    ) -> str:
        provider = provider.strip().lower()
        account = self._api_account(provider)

        secret = self._get_secret(account)
        if secret:
            return secret

        if provider == "openai":
            return (
                EnvironmentSecretProvider().get_secret(
                    "OPENAI_API_KEY"
                )
                or ""
            )

        if provider == "gemini":
            return (
                EnvironmentSecretProvider().get_secret(
                    "GEMINI_API_KEY"
                )
                or read_setting(
                    "GOOGLE_API_KEY"
                )
                or ""
            )

        if provider == "google":
            return read_setting(
                "GOOGLE_PLACES_API_KEY"
            )

        return ""

    def set_api_key(
        self,
        provider: str,
        api_key: str,
    ) -> None:
        account = self._api_account(
            provider.strip().lower()
        )

        value = api_key.strip()

        if not value:
            self._delete_secret(account)
            return

        self._set_secret(
            account,
            value,
        )

    def delete_api_key(
        self,
        provider: str,
    ) -> None:
        self._delete_secret(
            self._api_account(
                provider.strip().lower()
            )
        )

    def test_openai_key(
        self,
        api_key: str | None = None,
    ) -> tuple[bool, str]:
        key = (
            api_key
            or self.get_api_key("openai")
        ).strip()

        if not key:
            return (
                False,
                "Chave da OpenAI nÃ£o configurada.",
            )

        try:
            from openai import (
                AuthenticationError,
                OpenAI,
            )
        except ImportError:
            return (
                False,
                "A biblioteca openai nÃ£o estÃ¡ instalada.",
            )

        try:
            OpenAI(
                api_key=key
            ).models.list()
        except AuthenticationError:
            return (
                False,
                "Chave da OpenAI invÃ¡lida ou sem autenticaÃ§Ã£o.",
            )
        except Exception as exc:
            return (
                False,
                (
                    "NÃ£o foi possÃ­vel validar a chave: "
                    f"{exc}"
                ),
            )

        return (
            True,
            "Chave da OpenAI vÃ¡lida.",
        )

    def test_gemini_key(
        self,
        api_key: str | None = None,
    ) -> tuple[bool, str]:
        key = (
            api_key
            or self.get_api_key("gemini")
        ).strip()

        if not key:
            return (
                False,
                "Chave do Gemini não configurada.",
            )

        try:
            from urllib.error import HTTPError, URLError
            from urllib.request import Request, urlopen

            request = Request(
                "https://generativelanguage.googleapis.com/v1beta/models",
                headers={"x-goog-api-key": key},
                method="GET",
            )
            with urlopen(request, timeout=15) as response:
                if response.status != 200:
                    return (
                        False,
                        "A Gemini API não confirmou a chave.",
                    )
        except HTTPError as exc:
            return (
                False,
                f"Chave do Gemini rejeitada ({exc.code}).",
            )
        except (URLError, TimeoutError, OSError) as exc:
            return (
                False,
                f"Não foi possível validar o Gemini: {exc}",
            )

        return (
            True,
            "Chave do Gemini válida.",
        )

    def test_ollama(
        self,
        base_url: str | None = None,
    ) -> tuple[bool, str]:
        url = (
            base_url
            or self.ollama_base_url()
        ).strip().rstrip("/")

        try:
            from urllib.error import HTTPError, URLError
            from urllib.request import urlopen

            with urlopen(
                f"{url}/api/tags",
                timeout=5,
            ) as response:
                if response.status != 200:
                    return (
                        False,
                        "Ollama respondeu sem confirmar disponibilidade.",
                    )
        except HTTPError as exc:
            return (
                False,
                f"Ollama respondeu com HTTP {exc.code}.",
            )
        except (URLError, TimeoutError, OSError) as exc:
            return (
                False,
                f"Ollama local indisponível: {exc}",
            )

        return (
            True,
            "Ollama local disponível.",
        )

    def list_logins(
        self,
    ) -> list[LoginCredential]:
        rows = self._data.get(
            "logins",
            [],
        )

        result: list[LoginCredential] = []

        for row in (
            rows
            if isinstance(rows, list)
            else []
        ):
            if (
                not isinstance(row, dict)
                or not str(
                    row.get(
                        "service",
                        "",
                    )
                ).strip()
            ):
                continue

            result.append(
                LoginCredential(
                    service=str(
                        row.get(
                            "service",
                            "",
                        )
                    ).strip(),
                    url=str(
                        row.get(
                            "url",
                            "",
                        )
                    ).strip(),
                    username=str(
                        row.get(
                            "username",
                            "",
                        )
                    ).strip(),
                    notes=str(
                        row.get(
                            "notes",
                            "",
                        )
                    ).strip(),
                    server=str(row.get("server", "")).strip(),
                    port=self._safe_int(row.get("port", 0), default=0),
                    security=str(row.get("security", "")).strip(),
                    folder=str(row.get("folder", "")).strip(),
                    timeout_seconds=self._safe_int(
                        row.get("timeout_seconds", 60),
                        default=60,
                    ),
                )
            )

        return result

    def get_login(
        self,
        service: str,
    ) -> LoginCredential | None:
        """Return a login from its service/provider name."""
        target = service.strip().casefold()

        if not target:
            return None

        provider = (
            self._login_provider_registry.get(
                target
            )
        )

        accepted_names = {target}

        if provider is not None:
            accepted_names.update(
                {
                    provider.provider_id.casefold(),
                    provider.display_name.casefold(),
                }
            )

        for credential in self.list_logins():
            if (
                credential.service.strip().casefold()
                in accepted_names
            ):
                return credential

        return None

    def save_login(
        self,
        credential: LoginCredential,
        password: str | None = None,
    ) -> None:
        service = credential.service.strip()

        if not service:
            raise ValueError(
                "Informe o nome do serviÃ§o."
            )

        provider = (
            self._login_provider_registry.get(
                service
            )
        )

        if provider is not None:
            service = provider.display_name

        normalized = LoginCredential(
            service=service,
            url=credential.url.strip(),
            username=credential.username.strip(),
            notes=credential.notes.strip(),
            server=credential.server.strip(),
            port=max(int(credential.port or 0), 0),
            security=credential.security.strip().upper(),
            folder=credential.folder.strip(),
            timeout_seconds=max(int(credential.timeout_seconds or 60), 1),
        )

        rows = [
            item
            for item in self.list_logins()
            if item.service.casefold()
            != service.casefold()
        ]

        rows.append(normalized)
        rows.sort(
            key=lambda item: item.service.casefold()
        )

        self._data["logins"] = [
            asdict(item)
            for item in rows
        ]

        self._save()

        if password is not None:
            if password:
                self._set_secret(
                    self._login_account(
                        service
                    ),
                    password,
                )
            else:
                self._delete_secret(
                    self._login_account(
                        service
                    )
                )

    def login_password(
        self,
        service: str,
    ) -> str:
        credential = self.get_login(service)

        canonical_service = (
            credential.service
            if credential is not None
            else service.strip()
        )

        return self._get_secret(
            self._login_account(
                canonical_service
            )
        )

    def resolve_login_for_url(
        self,
        url: str,
    ) -> ResolvedLoginCredential | None:
        """Resolve one saved credential from a changing vacancy URL."""
        provider = (
            self._login_provider_registry.identify(
                url
            )
        )

        if provider is None:
            return None

        credential = (
            self.get_login(
                provider.provider_id
            )
        )

        if credential is None:
            credential = (
                self.get_login(
                    provider.display_name
                )
            )

        if credential is None:
            return None

        password = self.login_password(
            credential.service
        )

        return ResolvedLoginCredential(
            provider=provider,
            credential=credential,
            password=password,
        )

    def has_login_for_url(
        self,
        url: str,
    ) -> bool:
        """Return whether the URL has a configured provider credential."""
        return (
            self.resolve_login_for_url(url)
            is not None
        )

    def delete_login(
        self,
        service: str,
    ) -> None:
        credential = self.get_login(service)

        canonical_service = (
            credential.service
            if credential is not None
            else service.strip()
        )

        target = canonical_service.casefold()

        rows = [
            item
            for item in self.list_logins()
            if item.service.casefold()
            != target
        ]

        self._data["logins"] = [
            asdict(item)
            for item in rows
        ]

        self._save()

        self._delete_secret(
            self._login_account(
                canonical_service
            )
        )

    @staticmethod
    def _imap_mailbox_name(raw: bytes | str) -> str:
        text = (
            raw.decode('utf-8', errors='replace')
            if isinstance(raw, bytes)
            else str(raw)
        ).strip()
        if not text:
            return ''
        if '"' in text:
            quoted = re.findall(r'"([^"]*)"', text)
            if quoted:
                return quoted[-1].strip()
        parts = text.split()
        return parts[-1].strip('"') if parts else ''

    @classmethod
    def _imap_mailboxes(cls, client: object) -> tuple[str, ...]:
        status, rows = client.list()
        if status != 'OK' or not rows:
            return ()
        names = []
        for row in rows:
            name = cls._imap_mailbox_name(row)
            if name:
                names.append(name)
        return tuple(names)

    @classmethod
    def _resolve_imap_folder(
        cls,
        client: object,
        requested_folder: str,
    ) -> str | None:
        requested = requested_folder.strip()
        if not requested:
            return None
        mailboxes = cls._imap_mailboxes(client)
        requested_cf = requested.casefold()
        for mailbox in mailboxes:
            if mailbox.casefold() == requested_cf:
                return mailbox
        for mailbox in mailboxes:
            normalized = mailbox.replace('\\', '/').replace('.', '/')
            leaf = normalized.rsplit('/', 1)[-1].strip()
            if leaf.casefold() == requested_cf:
                return mailbox
        return None

    @classmethod
    def _find_imap_mailbox_by_sender(
        cls,
        client: object,
        sender: str,
    ) -> str | None:
        mailboxes = cls._imap_mailboxes(client)
        ordered = sorted(
            mailboxes,
            key=lambda mailbox: (
                'gupy' not in mailbox.casefold(),
                mailbox.casefold(),
            ),
        )
        for mailbox in ordered:
            try:
                status, _ = client.select(
                    f'"{mailbox}"',
                    readonly=True,
                )
            except Exception:
                continue
            if status != 'OK':
                continue
            try:
                status, data = client.search(
                    None,
                    'FROM',
                    f'"{sender}"',
                )
            except Exception:
                continue
            if status != 'OK' or not data:
                continue
            ids = data[0]
            if isinstance(ids, bytes):
                has_messages = bool(ids.strip())
            else:
                has_messages = bool(str(ids).strip())
            if has_messages:
                return mailbox
        return None

    def test_imap_login(
        self,
        credential: LoginCredential,
        password: str | None = None,
    ) -> tuple[bool, str]:
        """Validate IMAP authentication and the exact configured mailbox."""
        import imaplib

        host = credential.server.strip()
        username = credential.username.strip()
        folder = credential.folder.strip()
        secret = (
            password
            if password is not None
            else self.login_password(credential.service)
        )
        security = credential.security.strip().upper() or "SSL/TLS"
        port = int(
            credential.port
            or (993 if security == "SSL/TLS" else 143)
        )
        timeout = max(int(credential.timeout_seconds or 60), 1)

        if not host:
            return False, "Informe o servidor IMAP."
        if not username:
            return False, "Informe o e-mail/usuÃ¡rio IMAP."
        if not folder:
            return False, "Informe a pasta IMAP."
        if not secret:
            return False, "Informe a senha do e-mail."
        if security not in {"SSL/TLS", "STARTTLS", "NENHUMA"}:
            return False, "SeguranÃ§a IMAP invÃ¡lida."

        client = None
        try:
            if security == "SSL/TLS":
                client = imaplib.IMAP4_SSL(
                    host,
                    port,
                    timeout=timeout,
                )
            else:
                client = imaplib.IMAP4(
                    host,
                    port,
                    timeout=timeout,
                )
                if security == "STARTTLS":
                    client.starttls()

            status, _ = client.login(username, secret)
            if status != "OK":
                return False, "O servidor IMAP recusou a autenticaÃ§Ã£o."

            mailbox = "INBOX" if folder.casefold() == "inbox" else folder
            status, _ = client.select(mailbox, readonly=True)
            if status != "OK":
                return (
                    False,
                    "A conexÃ£o IMAP funcionou, mas a pasta configurada "
                    f"nÃ£o pÃ´de ser aberta: {folder}",
                )

            return (
                True,
                "ConexÃ£o IMAP realizada com sucesso. "
                f"Pasta configurada selecionada: {mailbox}",
            )
        except (imaplib.IMAP4.error, OSError) as exc:
            return False, f"Falha na conexÃ£o IMAP: {exc}"
        finally:
            if client is not None:
                try:
                    client.logout()
                except Exception as exc:
                    logging.getLogger(__name__).debug("Falha ao encerrar a sessão IMAP: %s", exc)

    def get_imap_login(
        self,
        service: str = "Terra IMAP",
    ) -> tuple[LoginCredential, str] | None:
        """Return one complete IMAP credential, including its protected password."""
        credential = self.get_login(service)
        if credential is None:
            return None
        return credential, self.login_password(credential.service)

    def diagnostic_snapshot(
        self,
    ) -> dict[str, str]:
        return {
            "Arquivo de configuraÃ§Ãµes": str(
                self._settings_path
            ),
            "InicializaÃ§Ã£o": (
                "Maximizado"
                if self.startup_mode()
                == "maximized"
                else "Minimizado"
            ),
            "Navegador LinkedIn": (
                "Segundo plano"
                if self.browser_headless()
                else "VisÃ­vel"
            ),
            "OpenAI": (
                "Configurada"
                if self.get_api_key(
                    "openai"
                )
                else "NÃ£o configurada"
            ),
            "Google": (
                "Configurada"
                if self.get_api_key(
                    "google"
                )
                else "NÃ£o configurada"
            ),
            "Logins cadastrados": str(
                len(
                    self.list_logins()
                )
            ),
        }

    def _load(
        self,
    ) -> dict[str, Any]:
        if not self._settings_path.exists():
            return {}

        try:
            value = json.loads(
                self._settings_path.read_text(
                    encoding="utf-8"
                )
            )
        except (
            OSError,
            json.JSONDecodeError,
        ):
            return {}

        return (
            value
            if isinstance(
                value,
                dict,
            )
            else {}
        )

    def _save(
        self,
    ) -> None:
        temporary = (
            self._settings_path.with_suffix(
                ".tmp"
            )
        )

        temporary.write_text(
            json.dumps(
                self._data,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        temporary.replace(
            self._settings_path
        )

    @staticmethod
    def _safe_int(value: object, *, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _api_account(
        provider: str,
    ) -> str:
        accounts = {
            "openai": SettingsService.OPENAI_KEY,
            "gemini": SettingsService.GEMINI_KEY,
            "google": SettingsService.GOOGLE_KEY,
        }

        try:
            return accounts[provider]
        except KeyError as exc:
            raise ValueError(

                    "Provedor de API nÃ£o suportado: "
                    f"{provider}"

            ) from exc

    @staticmethod
    def _login_account(
        service: str,
    ) -> str:
        return (
            f"login:{service.casefold()}"
        )

    def _get_secret(
        self,
        account: str,
    ) -> str:
        keyring = self._keyring()

        return (
            keyring.get_password(
                self.APP_KEYRING_SERVICE,
                account,
            )
            or ""
        )

    def _set_secret(
        self,
        account: str,
        value: str,
    ) -> None:
        keyring = self._keyring()

        keyring.set_password(
            self.APP_KEYRING_SERVICE,
            account,
            value,
        )

    def _delete_secret(
        self,
        account: str,
    ) -> None:
        keyring = self._keyring()

        try:
            keyring.delete_password(
                self.APP_KEYRING_SERVICE,
                account,
            )
        except Exception:
            return

    @staticmethod
    def _keyring():
        try:
            import keyring
        except ImportError as exc:
            raise RuntimeError(

                    "O pacote keyring nÃ£o estÃ¡ instalado. "
                    "Instale as dependÃªncias do projeto."

            ) from exc

        return keyring
