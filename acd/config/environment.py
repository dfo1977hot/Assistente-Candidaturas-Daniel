"""Environment configuration."""

from __future__ import annotations

from enum import StrEnum


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


CURRENT_ENVIRONMENT = Environment.DEVELOPMENT