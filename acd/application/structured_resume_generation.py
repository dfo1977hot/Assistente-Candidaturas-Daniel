"""Application-safe contracts for native structured resume generation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from acd.application.query_ports import VacancyQueryDTO
from acd.application.structured_resume_snapshot import StructuredResumeSnapshot


class StructuredResumeProviderStatus(StrEnum):
    """Outcomes exposed by a native structured-output provider."""

    SUCCESS = "success"
    STRUCTURED_SOURCE_REQUIRED = "structured_source_required"
    UNSUPPORTED = "unsupported"
    INVALID_RESPONSE = "invalid_response"
    UNSUPPORTED_SCHEMA = "unsupported_schema"
    TIMEOUT = "timeout"
    PROVIDER_ERROR = "provider_error"
    CONFIGURATION_REQUIRED = "configuration_required"


@dataclass(frozen=True)
class StructuredGenerationCapabilities:
    """Declared provider capabilities, without capability probing by execution."""

    supports_structured_resume: bool
    supports_json_schema: bool
    supported_schema_versions: tuple[int, ...]
    provider_name: str
    model_name: str | None = None


@dataclass(frozen=True)
class StructuredResumeProviderRequest:
    """Input for native, schema-constrained structured resume generation."""

    source_snapshot: StructuredResumeSnapshot
    vacancy: VacancyQueryDTO
    optimization_guidance: tuple[str, ...] = ()
    language: str = "pt-BR"


@dataclass(frozen=True)
class StructuredResumeProviderResult:
    """Provider response after native structured output processing."""

    status: StructuredResumeProviderStatus
    structured_resume: StructuredResumeSnapshot | None = None
    explanation: str | None = None
    provider_name: str | None = None
    model_name: str | None = None
    request_id: str | None = None
    message: str | None = None


class StructuredResumeGenerationPort(Protocol):
    """Port for providers that natively enforce structured resume output."""

    def get_capabilities(self) -> StructuredGenerationCapabilities:
        """Return declared capabilities without making a remote request."""

    def generate_structured_resume(
        self, request: StructuredResumeProviderRequest
    ) -> StructuredResumeProviderResult:
        """Request one structured result; never return arbitrary textual content."""


def validate_structured_generation_eligibility(
    source_snapshot: StructuredResumeSnapshot | None,
    capabilities: StructuredGenerationCapabilities,
) -> StructuredResumeProviderStatus:
    """Validate preconditions before a future generation use case calls a provider."""
    if source_snapshot is None:
        return StructuredResumeProviderStatus.STRUCTURED_SOURCE_REQUIRED
    if not capabilities.supports_structured_resume or not capabilities.supports_json_schema:
        return StructuredResumeProviderStatus.UNSUPPORTED
    if source_snapshot.schema_version not in capabilities.supported_schema_versions:
        return StructuredResumeProviderStatus.UNSUPPORTED_SCHEMA
    return StructuredResumeProviderStatus.SUCCESS
