"""Registry for login providers recognized by the ACD."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class LoginProvider:
    """Canonical identity of one external authentication provider."""

    provider_id: str
    display_name: str
    domains: tuple[str, ...]


class LoginProviderRegistry:
    """Resolve provider identities and vacancy URLs."""

    _PROVIDERS = (
        LoginProvider(
            provider_id="gupy",
            display_name="Gupy",
            domains=("gupy.io",),
        ),
        LoginProvider(
            provider_id="terra_imap",
            display_name="Terra IMAP",
            domains=(),
        ),
    )

    def identify(self, url: str) -> LoginProvider | None:
        """Return the provider associated with a URL, when supported."""
        hostname = self._hostname(url)
        if not hostname:
            return None

        for provider in self._PROVIDERS:
            if any(
                hostname == domain
                or hostname.endswith(f".{domain}")
                for domain in provider.domains
            ):
                return provider

        return None

    def get(self, provider_id: str) -> LoginProvider | None:
        """Return one provider from its stable identifier or display name."""
        normalized = provider_id.strip().casefold()

        for provider in self._PROVIDERS:
            if normalized in {
                provider.provider_id.casefold(),
                provider.display_name.casefold(),
            }:
                return provider

        return None

    def list_providers(self) -> tuple[LoginProvider, ...]:
        """Return all providers available for login configuration."""
        return self._PROVIDERS

    @staticmethod
    def _hostname(url: str) -> str:
        value = url.strip()
        if not value:
            return ""

        if "://" not in value:
            value = f"https://{value}"

        try:
            hostname = urlparse(value).hostname
        except ValueError:
            return ""

        return (hostname or "").strip(".").casefold()
