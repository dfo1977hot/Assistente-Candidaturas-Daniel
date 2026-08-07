"""Defensive redaction for observability payloads."""

from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any

REDACTED = "[REDACTED]"
MAX_TEXT_LENGTH = 512
_SECRET_KEYS = re.compile(
    r"(password|passwd|secret|token|api[_-]?key|authorization|cookie|connection[_-]?string|prompt|response|resume|curricul|cover[_-]?letter)",
    re.IGNORECASE,
)
_PATTERNS = (
    re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"),
    re.compile(r"\b\d{1,2}\.\d{3}\.\d{3}-[\dXx]\b"),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"(?<!\d)(?:\+?\d{1,3}\s*)?(?:\(?\d{2}\)?\s*)?\d{4,5}[-\s]?\d{4}(?!\d)"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b", re.IGNORECASE),
    re.compile(r"(?i)(password|passwd|token|api[_-]?key|authorization|cookie)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://[^\s/@:]+:[^\s/@]+@[^\s]+"),
)


def sanitize_text(value: object) -> str:
    text = "".join(
        character if ord(character) >= 32 or character == "\t" else " "
        for character in str(value)
    )
    for pattern in _PATTERNS:
        text = pattern.sub(REDACTED, text)
    if len(text) > MAX_TEXT_LENGTH:
        text = f"{text[:MAX_TEXT_LENGTH]}…[TRUNCATED]"
    return text


def sanitize_mapping(values: Mapping[str, Any] | None) -> dict[str, Any]:
    if not values:
        return {}
    result: dict[str, Any] = {}
    for raw_key, value in values.items():
        key = sanitize_text(raw_key)
        if _SECRET_KEYS.search(key):
            result[key] = REDACTED
        elif value is None or isinstance(value, bool | int | float):
            result[key] = value
        elif isinstance(value, Mapping):
            result[key] = sanitize_mapping(value)
        elif isinstance(value, (list, tuple, set, frozenset)):
            result[key] = [sanitize_text(item) for item in list(value)[:20]]
        else:
            result[key] = sanitize_text(value)
    return result
