"""Single JSON Schema definition for the structured resume snapshot v1."""

from __future__ import annotations

from typing import Any


class StructuredResumeJsonSchema:
    """Build the native-provider output schema consistent with the v1 codec."""

    @staticmethod
    def build() -> dict[str, Any]:
        """Return the complete, strict JSON Schema used by structured providers."""
        nullable_string = {"type": ["string", "null"]}
        string_array = {"type": "array", "items": {"type": "string"}}
        identity = StructuredResumeJsonSchema._object(
            {
                "full_name": nullable_string,
                "professional_title": nullable_string,
                "location": nullable_string,
            }
        )
        contact = StructuredResumeJsonSchema._object(
            {
                "email": nullable_string,
                "phone": nullable_string,
                "linkedin": nullable_string,
                "portfolio": nullable_string,
                "website": nullable_string,
            }
        )
        experience = StructuredResumeJsonSchema._object(
            {
                "company": nullable_string,
                "role": nullable_string,
                "location": nullable_string,
                "start_date": nullable_string,
                "end_date": nullable_string,
                "is_current": {"type": "boolean"},
                "summary": nullable_string,
                "achievements": string_array,
            }
        )
        education = StructuredResumeJsonSchema._object(
            {
                "institution": nullable_string,
                "degree": nullable_string,
                "field": nullable_string,
                "start_date": nullable_string,
                "end_date": nullable_string,
                "status": nullable_string,
                "details": nullable_string,
            }
        )
        certification = StructuredResumeJsonSchema._object(
            {"name": nullable_string, "issuer": nullable_string, "issued_date": nullable_string, "credential_id": nullable_string, "url": nullable_string}
        )
        course = StructuredResumeJsonSchema._object(
            {"name": nullable_string, "provider": nullable_string, "completed_date": nullable_string, "details": nullable_string}
        )
        language = StructuredResumeJsonSchema._object(
            {"name": nullable_string, "proficiency": nullable_string}
        )
        project = StructuredResumeJsonSchema._object(
            {"name": nullable_string, "description": nullable_string, "url": nullable_string, "highlights": string_array}
        )
        additional_section = StructuredResumeJsonSchema._object(
            {"title": nullable_string, "paragraphs": string_array, "items": string_array, "order": {"type": "integer"}}
        )
        return StructuredResumeJsonSchema._object(
            {
                "schema_version": {"const": 1, "type": "integer"},
                "identity": identity,
                "contact": contact,
                "summary": nullable_string,
                "skills": string_array,
                "experiences": {"type": "array", "items": experience},
                "education": {"type": "array", "items": education},
                "certifications": {"type": "array", "items": certification},
                "courses": {"type": "array", "items": course},
                "languages": {"type": "array", "items": language},
                "projects": {"type": "array", "items": project},
                "additional_sections": {"type": "array", "items": additional_section},
            }
        )

    @staticmethod
    def _object(properties: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": properties,
            "required": list(properties),
            "additionalProperties": False,
        }
