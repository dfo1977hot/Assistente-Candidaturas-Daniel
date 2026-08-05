"""Tests for structured curriculum read adaptation."""

from __future__ import annotations

from types import SimpleNamespace

from acd.application.structured_resume_snapshot import StructuredResumeContentStatus
from acd.infrastructure.query_adapters.resume_query_adapter import ResumeQueryAdapter


class _Repository:
    def __init__(self, structured_content_json: str | None) -> None:
        self._curriculum = SimpleNamespace(
            id=1,
            name="Daniel",
            version="v1",
            language="pt-BR",
            description="textual",
            structured_content_json=structured_content_json,
        )

    def get_by_id(self, _curriculum_id: int):
        return self._curriculum

    def get_versions(self, _curriculum_id: int):
        return []


def test_resume_adapter_returns_immutable_snapshot_for_valid_json() -> None:
    payload = '{"schema_version":1,"identity":{"full_name":null,"professional_title":null,"location":null},"contact":{"email":null,"phone":null,"linkedin":null,"portfolio":null,"website":null},"summary":null,"skills":["Python"],"experiences":[],"education":[],"certifications":[],"courses":[],"languages":[],"projects":[],"additional_sections":[]}'

    resume = ResumeQueryAdapter(_Repository(payload)).get_by_id(1)

    assert resume is not None
    assert resume.description == "textual"
    assert resume.structured_content_status is StructuredResumeContentStatus.AVAILABLE
    assert resume.structured_resume is not None
    assert resume.structured_resume.skills == ("Python",)


def test_resume_adapter_keeps_text_for_unsupported_schema() -> None:
    resume = ResumeQueryAdapter(_Repository('{"schema_version":999}')).get_by_id(1)

    assert resume is not None
    assert resume.description == "textual"
    assert resume.structured_resume is None
    assert resume.structured_content_status is StructuredResumeContentStatus.UNSUPPORTED_SCHEMA
