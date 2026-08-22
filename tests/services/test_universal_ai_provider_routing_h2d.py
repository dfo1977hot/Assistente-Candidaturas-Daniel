from __future__ import annotations

import ast
from pathlib import Path

from acd.services.recruiter_email_research_service import (
    RecruiterEmailResearchRequest,
    RecruiterEmailResearchService,
)
from acd.services.salary_research_service import (
    SalaryResearchRequest,
    SalaryResearchService,
)


class _FakeAIProvider:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls: list[dict[str, object]] = []

    def generate_text(self, **kwargs: object) -> str:
        self.calls.append(dict(kwargs))
        return self.response


def test_salary_research_uses_injected_ai_provider(tmp_path: Path) -> None:
    provider = _FakeAIProvider(
        '{"values": [12000, 13500, 15000], "median_salary": 13500, "currency": "BRL"}'
    )
    service = SalaryResearchService(
        ai_provider=provider,  # type: ignore[arg-type]
        cache_path=tmp_path / "salary.json",
    )

    result = service.research(
        SalaryResearchRequest(
            title="Coordenador de Logística",
            location="Guarulhos - SP",
            work_model="Presencial",
            employment_type="CLT",
        ),
        force_refresh=True,
    )

    assert result.salary_min == 13500
    assert result.salary_max == 13500
    assert len(provider.calls) == 1
    assert provider.calls[0]["model"] == "salary-research"


def test_recruiter_email_research_uses_injected_ai_provider() -> None:
    provider = _FakeAIProvider('{"email": "recrutamento@empresa.com.br"}')
    service = RecruiterEmailResearchService(
        ai_provider=provider,  # type: ignore[arg-type]
    )

    result = service.research(
        RecruiterEmailResearchRequest(
            company_name="Empresa",
            job_title="Coordenador de Logística",
        )
    )

    assert result == "recrutamento@empresa.com.br"
    assert len(provider.calls) == 1
    assert provider.calls[0]["model"] == "recruiter-email-research"


def test_common_ai_services_do_not_import_openai_directly() -> None:
    paths = (
        "acd/services/salary_research_service.py",
        "acd/services/cover_letter_service.py",
        "acd/services/recruiter_email_research_service.py",
        "acd/services/linkedin_job_import_service.py",
    )

    for filename in paths:
        tree = ast.parse(Path(filename).read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        assert "openai" not in imports, filename


def test_composition_root_shares_configured_ai_provider() -> None:
    source = Path("acd/desktop_composition_root.py").read_text(encoding="utf-8")

    assert "ai_provider = SettingsConfiguredAIProvider(settings_service)" in source
    assert "SalaryResearchService(" in source
    assert "RecruiterEmailResearchService(" in source
    assert "LinkedInJobImportService(" in source
    assert "ai_provider=ai_provider" in source
