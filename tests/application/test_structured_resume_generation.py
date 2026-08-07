"""Tests for the Application structured-resume provider boundary."""

from __future__ import annotations

from acd.application.query_ports import VacancyQueryDTO
from acd.application.structured_resume_generation import (
    StructuredGenerationCapabilities,
    StructuredResumeProviderRequest,
    StructuredResumeProviderResult,
    StructuredResumeProviderStatus,
    validate_structured_generation_eligibility,
)
from acd.application.structured_resume_snapshot import StructuredResumeSnapshotCodec
from acd.infrastructure.ai.structured_resume_generation_provider import (
    FakeStructuredResumeGenerationProvider,
    UnsupportedStructuredResumeGenerationProvider,
)


def _snapshot():
    return StructuredResumeSnapshotCodec().from_payload(
        {
            "schema_version": 1,
            "identity": {"full_name": None, "professional_title": None, "location": None},
            "contact": {"email": None, "phone": None, "linkedin": None, "portfolio": None, "website": None},
            "summary": None, "skills": [], "experiences": [], "education": [], "certifications": [],
            "courses": [], "languages": [], "projects": [], "additional_sections": [],
        }
    )


def _request() -> StructuredResumeProviderRequest:
    return StructuredResumeProviderRequest(
        _snapshot(), VacancyQueryDTO(2, "Engineer", 3, "Remote"), ("Preserve facts",)
    )


def test_fake_provider_uses_only_the_explicit_structured_contract() -> None:
    request = _request()
    result = StructuredResumeProviderResult(
        StructuredResumeProviderStatus.SUCCESS, structured_resume=request.source_snapshot
    )
    provider = FakeStructuredResumeGenerationProvider(result)

    assert provider.get_capabilities().supports_json_schema
    assert provider.generate_structured_resume(request) is result
    assert provider.requests == [request]
    assert not hasattr(provider, "generate_text")


def test_eligibility_blocks_legacy_source_and_unsupported_provider_before_generation() -> None:
    supported = StructuredGenerationCapabilities(True, True, (1,), "fake")
    unsupported = StructuredGenerationCapabilities(False, False, (), "unconfigured")

    assert (
        validate_structured_generation_eligibility(None, supported)
        is StructuredResumeProviderStatus.STRUCTURED_SOURCE_REQUIRED
    )
    assert (
        validate_structured_generation_eligibility(_snapshot(), unsupported)
        is StructuredResumeProviderStatus.UNSUPPORTED
    )
    assert (
        validate_structured_generation_eligibility(
            _snapshot(), StructuredGenerationCapabilities(True, True, (2,), "fake")
        )
        is StructuredResumeProviderStatus.UNSUPPORTED_SCHEMA
    )


def test_unsupported_provider_is_safe_and_makes_no_external_call() -> None:
    provider = UnsupportedStructuredResumeGenerationProvider()

    result = provider.generate_structured_resume(_request())

    assert not provider.get_capabilities().supports_structured_resume
    assert result.status is StructuredResumeProviderStatus.UNSUPPORTED
    assert result.structured_resume is None
