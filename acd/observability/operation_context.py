"""Context-local identifiers for correlated operations."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
import re
import uuid

_correlation_id: ContextVar[str | None] = ContextVar("acd_correlation_id", default=None)
_operation_id: ContextVar[str | None] = ContextVar("acd_operation_id", default=None)
_user_action: ContextVar[str | None] = ContextVar("acd_user_action", default=None)
_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$")


def _validated_identifier(value: str | None) -> str:
    if value is not None and _SAFE_IDENTIFIER.fullmatch(value):
        return value
    return str(uuid.uuid4())


@dataclass(frozen=True, slots=True)
class ObservationContext:
    correlation_id: str
    operation_id: str | None
    user_action: str | None


def observation_context() -> ObservationContext:
    correlation = _correlation_id.get() or str(uuid.uuid4())
    if _correlation_id.get() is None:
        _correlation_id.set(correlation)
    return ObservationContext(correlation, _operation_id.get(), _user_action.get())


@contextmanager
def bind_observation_context(
    *,
    correlation_id: str | None = None,
    operation_id: str | None = None,
    user_action: str | None = None,
) -> Iterator[ObservationContext]:
    """Bind identifiers for one operation and restore the previous context."""
    correlation_token = _correlation_id.set(_validated_identifier(correlation_id))
    operation_token = _operation_id.set(_validated_identifier(operation_id))
    action_token = _user_action.set(user_action)
    try:
        yield observation_context()
    finally:
        _user_action.reset(action_token)
        _operation_id.reset(operation_token)
        _correlation_id.reset(correlation_token)
