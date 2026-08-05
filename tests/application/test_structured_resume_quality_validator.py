"""Tests for deterministic, read-only structured resume quality validation."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from acd.application.structured_resume_quality_validation import (
    StructuredResumeQualityCategory,
    StructuredResumeQualitySeverity,
    StructuredResumeQualityValidator,
)
from acd.application.structured_resume_snapshot import (
    StructuredResumeCertification,
    StructuredResumeContact,
    StructuredResumeEducation,
    StructuredResumeExperience,
    StructuredResumeIdentity,
    StructuredResumeLanguage,
    StructuredResumeSnapshot,
)


def _snapshot(**changes: object) -> StructuredResumeSnapshot:
    values: dict[str, object] = {
        "schema_version": 1,
        "identity": StructuredResumeIdentity("Daniel Silva", "Engineer"),
        "contact": StructuredResumeContact("daniel@example.com"),
        "summary": "Software engineer.",
        "skills": ("Python",),
        "experiences": (
            StructuredResumeExperience("ACD", "Engineer", start_date="2025-01", is_current=True),
        ),
    }
    values.update(changes)
    return StructuredResumeSnapshot(**values)  # type: ignore[arg-type]


def _codes(snapshot: StructuredResumeSnapshot) -> tuple[str, ...]:
    return tuple(issue.code for issue in StructuredResumeQualityValidator().validate(snapshot).issues)


def test_valid_snapshot_has_no_issues_and_full_score() -> None:
    result = StructuredResumeQualityValidator().validate(_snapshot())

    assert result.issues == ()
    assert result.is_valid
    assert result.score == 100
    assert (result.error_count, result.warning_count, result.info_count) == (0, 0, 0)


@pytest.mark.parametrize(
    ("snapshot", "code"),
    [
        (_snapshot(identity=StructuredResumeIdentity(" ")), "IDENTITY_NAME_REQUIRED"),
        (_snapshot(contact=StructuredResumeContact("invalid email")), "CONTACT_EMAIL_INVALID"),
        (_snapshot(skills=(" ",)), "SKILL_EMPTY"),
        (_snapshot(skills=("Python", " python  ")), "SKILL_DUPLICATE"),
        (_snapshot(experiences=(StructuredResumeExperience(None, "Engineer"),)), "EXPERIENCE_COMPANY_REQUIRED"),
        (_snapshot(experiences=(StructuredResumeExperience("ACD", None),)), "EXPERIENCE_ROLE_REQUIRED"),
        (_snapshot(experiences=(StructuredResumeExperience("ACD", "Engineer", start_date="2026-02", end_date="2025-01"),)), "EXPERIENCE_PERIOD_INVALID"),
        (_snapshot(experiences=(StructuredResumeExperience("ACD", "Engineer", start_date="2025-01"), StructuredResumeExperience("acd", " engineer ", start_date="2025-01"))), "EXPERIENCE_DUPLICATE"),
        (_snapshot(education=(StructuredResumeEducation("Uni", "BS", start_date="2020-01"), StructuredResumeEducation("uni", "bs", start_date="2020-01"))), "EDUCATION_DUPLICATE"),
        (_snapshot(certifications=(StructuredResumeCertification("AWS", "Amazon", "2024-01"), StructuredResumeCertification("aws", "amazon", "2024-01"))), "CERTIFICATION_DUPLICATE"),
        (_snapshot(languages=(StructuredResumeLanguage("Português", "Nativo"), StructuredResumeLanguage("português", "Nativo"))), "LANGUAGE_DUPLICATE"),
        (_snapshot(languages=(StructuredResumeLanguage("Português", "Nativo"), StructuredResumeLanguage("português", "Avançado"))), "LANGUAGE_CONFLICTING_PROFICIENCY"),
        (_snapshot(summary="TODO"), "CONTENT_PLACEHOLDER_DETECTED"),
        (_snapshot(summary="bad\x01content"), "CONTENT_CONTROL_CHARACTER"),
        (_snapshot(summary="Traceback (most recent call last):"), "CONTENT_TECHNICAL_ARTIFACT"),
        (_snapshot(experiences=(StructuredResumeExperience("New", "Engineer", start_date="2024-01"), StructuredResumeExperience("Old", "Engineer", start_date="2025-01"))), "CHRONOLOGY_ORDER_WARNING"),
        (_snapshot(identity=StructuredResumeIdentity(None), summary=None, skills=(), experiences=()), "EXPORT_MINIMUM_CONTENT_REQUIRED"),
    ],
)
def test_detects_each_required_rule(snapshot: StructuredResumeSnapshot, code: str) -> None:
    assert code in _codes(snapshot)


def test_issue_metadata_is_immutable_stable_and_ordered() -> None:
    result = StructuredResumeQualityValidator().validate(
        _snapshot(identity=StructuredResumeIdentity(None), skills=("", "Python", "python"))
    )

    assert result.issues[0].severity is StructuredResumeQualitySeverity.ERROR
    assert result.issues[0].category is StructuredResumeQualityCategory.EXPORTABILITY
    assert result.issues[0].code == "EXPORT_MINIMUM_CONTENT_REQUIRED"
    assert result.issues[0].recommendation
    with pytest.raises(FrozenInstanceError):
        result.issues[0].code = "OTHER"  # type: ignore[misc]


def test_score_counts_validity_and_input_are_deterministic_and_immutable() -> None:
    snapshot = _snapshot(identity=StructuredResumeIdentity(None), skills=("", "Python", "python"))
    before = snapshot
    validator = StructuredResumeQualityValidator()

    first = validator.validate(snapshot)
    second = validator.validate(snapshot)

    assert first == second
    assert snapshot == before
    assert not first.is_valid
    assert first.score == max(0, 100 - first.error_count * 20 - first.warning_count * 5 - first.info_count)
