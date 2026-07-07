from __future__ import annotations

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(UTC)