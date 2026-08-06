"""Validation for optional external HTTPS endpoints."""

from __future__ import annotations

import ipaddress
from urllib.parse import urlparse

from acd.security.security_errors import ExternalUrlRejectedError


def validate_external_https_url(value: str) -> str:
    """Allow only credential-free external HTTPS URLs."""
    if not value or len(value) > 2048 or any(ord(character) < 32 for character in value):
        raise ExternalUrlRejectedError("External URL is invalid")
    parsed = urlparse(value)
    if parsed.scheme.lower() != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ExternalUrlRejectedError("External URL must use credential-free HTTPS")
    hostname = parsed.hostname.lower().rstrip(".")
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise ExternalUrlRejectedError("Local network destination is not allowed")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return value
    if not address.is_global:
        raise ExternalUrlRejectedError("Non-public network destination is not allowed")
    return value

