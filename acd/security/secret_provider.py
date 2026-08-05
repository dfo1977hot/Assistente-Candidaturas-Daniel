"""Central, side-effect-free access to allowlisted process secrets."""

from __future__ import annotations

from collections.abc import Mapping
import os
from typing import Protocol

from acd.security.security_errors import SecretConfigurationError

ALLOWED_SECRET_NAMES = frozenset({"OPENAI_API_KEY"})
MAX_SECRET_LENGTH = 8192


class SecretProvider(Protocol):
    def get_secret(self, name: str, *, required: bool = False) -> str | None:
        """Return an allowlisted secret without exposing it in errors."""


class EnvironmentSecretProvider:
    """Read only explicit secret names from an injected or process mapping."""

    def __init__(self, values: Mapping[str, str] | None = None) -> None:
        self._values = os.environ if values is None else values

    def get_secret(self, name: str, *, required: bool = False) -> str | None:
        if name not in ALLOWED_SECRET_NAMES:
            raise SecretConfigurationError("Secret name is not authorized")
        value = self._values.get(name, "").strip()
        if not value:
            if required:
                raise SecretConfigurationError("Required secret is unavailable")
            return None
        if len(value) > MAX_SECRET_LENGTH or any(ord(character) < 32 for character in value):
            raise SecretConfigurationError("Secret value is invalid")
        return value


def read_setting(
    name: str,
    *,
    values: Mapping[str, str] | None = None,
    default: str = "",
    max_length: int = 512,
) -> str:
    """Read one non-secret integration setting with defensive bounds."""
    source = os.environ if values is None else values
    value = source.get(name, default).strip()
    if len(value) > max_length or any(ord(character) < 32 for character in value):
        raise SecretConfigurationError("Integration setting is invalid")
    return value

