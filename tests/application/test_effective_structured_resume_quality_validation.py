"""Tests for effective structured resume quality validation use case."""

from __future__ import annotations

from acd.application.application_resume_source import ApplicationResumeSource
from acd.application.effective_application_resume_use_case import (
    EffectiveApplicationResumeResult,
    EffectiveApplicationResumeStatus,
)
from acd.application.structured_resume_quality_validation import (
    EffectiveStructuredResumeQualityStatus,
    StructuredResumeQualityValidator,
    ValidateEffectiveStructuredResumeQualityRequest,
    ValidateEffectiveStructuredResumeQualityUseCase,
)
from acd.application.structured_resume_snapshot import (
    StructuredResumeContentStatus,
    StructuredResumeIdentity,
    StructuredResumeSnapshot,
)


class _Resolver:
    def __init__(self, result: EffectiveApplicationResumeResult) -> None:
        self.result = result
        self.requests: list[object] = []

    def execute(self, request: object) -> EffectiveApplicationResumeResult:
        self.requests.append(request)
        return self.result


class _Validator(StructuredResumeQualityValidator):
    def __init__(self) -> None:
        self.calls = 0

    def validate(self, snapshot: StructuredResumeSnapshot):
        self.calls += 1
        return super().validate(snapshot)


def _success(source: ApplicationResumeSource = ApplicationResumeSource.ORIGINAL) -> EffectiveApplicationResumeResult:
    return EffectiveApplicationResumeResult(
        EffectiveApplicationResumeStatus.SUCCESS,
        7,
        curriculum_id=10,
        resume_source=source,
        effective_resume_version_id=2 if source is ApplicationResumeSource.RESUME_VERSION else None,
        structured_resume=StructuredResumeSnapshot(1, identity=StructuredResumeIdentity("Daniel"), summary="Engineer"),
        structured_content_status=StructuredResumeContentStatus.AVAILABLE,
    )


def _use_case(resolver: _Resolver) -> ValidateEffectiveStructuredResumeQualityUseCase:
    return ValidateEffectiveStructuredResumeQualityUseCase(resolver, StructuredResumeQualityValidator())  # type: ignore[arg-type]


def test_validates_effective_original_once_without_side_effects() -> None:
    resolver = _Resolver(_success())
    validator = _Validator()
    result = ValidateEffectiveStructuredResumeQualityUseCase(resolver, validator).execute(ValidateEffectiveStructuredResumeQualityRequest(7))  # type: ignore[arg-type]

    assert result.status is EffectiveStructuredResumeQualityStatus.SUCCESS
    assert result.source is ApplicationResumeSource.ORIGINAL
    assert result.curriculum_id == 10
    assert result.resume_version_id is None
    assert result.is_valid
    assert result.summary == "Nenhum problema estrutural identificado."
    assert resolver.requests[0].application_id == 7
    assert validator.calls == 1


def test_validates_only_the_effective_adopted_version() -> None:
    resolver = _Resolver(_success(ApplicationResumeSource.RESUME_VERSION))
    result = ValidateEffectiveStructuredResumeQualityUseCase(resolver, StructuredResumeQualityValidator()).execute(ValidateEffectiveStructuredResumeQualityRequest(7))  # type: ignore[arg-type]

    assert result.status is EffectiveStructuredResumeQualityStatus.SUCCESS
    assert result.source is ApplicationResumeSource.RESUME_VERSION
    assert result.resume_version_id == 2


def test_maps_resolution_and_structured_content_failures_without_validation() -> None:
    missing = _Resolver(EffectiveApplicationResumeResult(EffectiveApplicationResumeStatus.APPLICATION_NOT_FOUND, 7))
    unavailable = _Resolver(_success())
    unavailable.result = EffectiveApplicationResumeResult(EffectiveApplicationResumeStatus.SUCCESS, 7)
    unsupported = _Resolver(_success())
    unsupported.result = EffectiveApplicationResumeResult(EffectiveApplicationResumeStatus.SUCCESS, 7, structured_content_status=StructuredResumeContentStatus.UNSUPPORTED_SCHEMA)

    assert _use_case(missing).execute(ValidateEffectiveStructuredResumeQualityRequest(7)).status is EffectiveStructuredResumeQualityStatus.APPLICATION_NOT_FOUND
    assert _use_case(unavailable).execute(ValidateEffectiveStructuredResumeQualityRequest(7)).status is EffectiveStructuredResumeQualityStatus.STRUCTURED_CONTENT_REQUIRED
    assert _use_case(unsupported).execute(ValidateEffectiveStructuredResumeQualityRequest(7)).status is EffectiveStructuredResumeQualityStatus.UNSUPPORTED_SCHEMA
