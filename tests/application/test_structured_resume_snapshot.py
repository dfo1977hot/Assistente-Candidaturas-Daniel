"""Tests for the immutable, versioned structured resume snapshot contract."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, asdict

import pytest

from acd.application.structured_resume_snapshot import (
    StructuredResumeContentStatus,
    StructuredResumeSnapshot,
    StructuredResumeSnapshotCodec,
    StructuredResumeValidationError,
    UnsupportedStructuredResumeSchemaError,
)


def _payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "identity": {"full_name": "Daniel", "professional_title": None, "location": "São Paulo"},
        "contact": {"email": "daniel@example.com", "phone": None, "linkedin": None, "portfolio": None, "website": None},
        "summary": "Resumo",
        "skills": ["Python", "SQL"],
        "experiences": [{"company": "Empresa A", "role": "Engineer", "location": None, "start_date": "2020-01", "end_date": None, "is_current": True, "summary": None, "achievements": ["Entrega"]}],
        "education": [{"institution": "USP", "degree": None, "field": None, "start_date": None, "end_date": None, "status": None, "details": None}],
        "certifications": [{"name": "AWS", "issuer": None, "issued_date": None, "credential_id": None, "url": None}],
        "courses": [{"name": "DDD", "provider": None, "completed_date": None, "details": None}],
        "languages": [{"name": "Português", "proficiency": "Nativo"}],
        "projects": [{"name": "ACD", "description": None, "url": None, "highlights": ["DDD"]}],
        "additional_sections": [{"title": "Publicações", "paragraphs": ["Artigo"], "items": [], "order": 2}],
    }


def test_codec_round_trip_is_canonical_unicode_and_immutable() -> None:
    codec = StructuredResumeSnapshotCodec()
    payload = _payload()

    snapshot = codec.from_payload(payload)
    serialized = codec.dumps(snapshot)

    assert codec.loads(serialized) == snapshot
    assert serialized == codec.dumps(snapshot)
    assert "São Paulo" in serialized
    assert snapshot.skills == ("Python", "SQL")
    assert snapshot.experiences[0].achievements == ("Entrega",)
    assert payload == _payload()
    with pytest.raises(FrozenInstanceError):
        snapshot.summary = "alterado"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("mutator", "error"),
    [
        (lambda payload: payload.pop("schema_version"), StructuredResumeValidationError),
        (lambda payload: payload.__setitem__("schema_version", 999), UnsupportedStructuredResumeSchemaError),
        (lambda payload: payload.__setitem__("unknown", "value"), StructuredResumeValidationError),
        (lambda payload: payload.__setitem__("skills", "Python"), StructuredResumeValidationError),
        (lambda payload: payload["experiences"].append({"company": "x"}), StructuredResumeValidationError),  # type: ignore[union-attr]
    ],
)
def test_codec_rejects_invalid_or_unknown_schema_payloads(mutator, error: type[Exception]) -> None:
    payload = _payload()
    mutator(payload)

    with pytest.raises(error):
        StructuredResumeSnapshotCodec().from_payload(payload)


def test_codec_rejects_malformed_json_and_reports_read_statuses() -> None:
    codec = StructuredResumeSnapshotCodec()

    with pytest.raises(StructuredResumeValidationError):
        codec.loads("{")

    assert codec.decode(None) == (None, StructuredResumeContentStatus.UNAVAILABLE)
    assert codec.decode("{")[1] is StructuredResumeContentStatus.INVALID
    assert codec.decode('{"schema_version":999}')[1] is StructuredResumeContentStatus.UNSUPPORTED_SCHEMA


def test_snapshot_requires_a_validated_model_for_serialization() -> None:
    codec = StructuredResumeSnapshotCodec()

    with pytest.raises(StructuredResumeValidationError):
        codec.dumps(object())  # type: ignore[arg-type]

    assert asdict(StructuredResumeSnapshot(schema_version=1))["skills"] == ()
