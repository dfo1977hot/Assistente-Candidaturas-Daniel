"""Tests for consistency between provider JSON Schema and the v1 codec."""

from __future__ import annotations

from acd.application.structured_resume_json_schema import StructuredResumeJsonSchema
from acd.application.structured_resume_snapshot import StructuredResumeSnapshot


def test_provider_schema_is_strict_and_matches_the_snapshot_envelope() -> None:
    schema = StructuredResumeJsonSchema.build()

    assert schema["additionalProperties"] is False
    assert schema["required"] == list(StructuredResumeSnapshot.__dataclass_fields__)
    assert schema["properties"]["schema_version"] == {"const": 1, "type": "integer"}
    assert schema["properties"]["identity"]["additionalProperties"] is False
    assert schema["properties"]["contact"]["properties"]["email"]["type"] == ["string", "null"]
    assert schema["properties"]["experiences"]["items"]["properties"]["achievements"]["type"] == "array"
    assert schema["properties"]["additional_sections"]["items"]["properties"]["order"]["type"] == "integer"
