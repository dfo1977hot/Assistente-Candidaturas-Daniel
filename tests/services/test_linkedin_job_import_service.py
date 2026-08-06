from __future__ import annotations

import json

import pytest

from acd.services.linkedin_job_import_service import (
    LinkedInJobImportError,
    LinkedInJobImportService,
)


def test_normalize_accepts_linkedin_job_url() -> None:
    url = "https://www.linkedin.com/jobs/view/1234567890/"
    assert LinkedInJobImportService.normalize_linkedin_job_url(url) == url


@pytest.mark.parametrize(
    "url",
    [
        "",
        "www.linkedin.com/jobs/view/1234567890",
        "https://example.com/jobs/view/1234567890",
        "https://www.linkedin.com/in/candidato",
    ],
)
def test_normalize_rejects_invalid_url(url: str) -> None:
    with pytest.raises(LinkedInJobImportError):
        LinkedInJobImportService.normalize_linkedin_job_url(url)


def test_extracts_output_text_from_responses_payload() -> None:
    payload = {
        "output": [
            {"type": "reasoning", "content": []},
            {
                "type": "message",
                "content": [{"type": "output_text", "text": '{"title":"Analista"}'}],
            },
        ]
    }
    assert LinkedInJobImportService._extract_output_text(payload) == '{"title":"Analista"}'


def test_converts_structured_data_without_inventing_values() -> None:
    data = {
        "title": "Analista de Logística",
        "company_name": "Empresa Exemplo",
        "location": "Guarulhos, SP",
        "work_model": "Híbrido",
        "employment_type": "CLT",
        "salary_min": 8000,
        "salary_max": 10000,
        "currency": "BRL",
        "requirements": ["Excel", "Power BI"],
        "confidence": "Alta",
    }
    result = LinkedInJobImportService._to_result(
        data,
        "https://www.linkedin.com/jobs/view/1234567890/",
    )
    assert result.title == "Analista de Logística"
    assert result.company_name == "Empresa Exemplo"
    assert result.salary_min == 8000
    assert result.requirements == ("Excel", "Power BI")
    assert result.linkedin_job_id == "1234567890"


def test_parses_json_inside_markdown_fence() -> None:
    parsed = LinkedInJobImportService._parse_structured_json(
        "```json\n" + json.dumps({"title": "Coordenador"}) + "\n```"
    )
    assert parsed["title"] == "Coordenador"
