"""Explicit trust-boundary controls for local ACD operations."""

from acd.security.external_content import ExternalFilePolicy, ValidatedExternalFile
from acd.security.network_policy import validate_external_https_url
from acd.security.secret_provider import EnvironmentSecretProvider, SecretProvider
from acd.security.secure_paths import AuthorizedPathPolicy
from acd.security.security_errors import (
    ExternalFileRejectedError,
    ExternalUrlRejectedError,
    PathRejectedError,
    PluginRejectedError,
    SecretConfigurationError,
)

__all__ = [
    "AuthorizedPathPolicy",
    "EnvironmentSecretProvider",
    "ExternalFilePolicy",
    "ExternalFileRejectedError",
    "ExternalUrlRejectedError",
    "PathRejectedError",
    "PluginRejectedError",
    "SecretConfigurationError",
    "SecretProvider",
    "ValidatedExternalFile",
    "validate_external_https_url",
]

