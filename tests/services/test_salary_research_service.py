from concurrent.futures import ThreadPoolExecutor
import json
from types import SimpleNamespace

import pytest

from acd.services.salary_research_service import (
    SalaryResearchRequest,
    SalaryResearchService,
)


class _Responses:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.last_kwargs = None
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        self.last_kwargs = kwargs
        return SimpleNamespace(output_text=json.dumps(self.payload))


class _Client:
    def __init__(self, payload: dict) -> None:
        self.responses = _Responses(payload)


def test_research_uses_title_location_model_and_employment_type(tmp_path) -> None:
    client = _Client(
        {
        "median_salary": 10500,
        "currency": "BRL",
        "period": "mensal",
        }
    )
    service = SalaryResearchService(
        client=client,
        model="test-model",
        cache_path=tmp_path / "cache.json",
    )

    result = service.research(
        SalaryResearchRequest(
            title="Coordenador de Logística",
            location="Guarulhos, SP, Brasil",
            work_model="Presencial",
            employment_type="CLT",
        )
    )

    prompt = client.responses.last_kwargs["input"]
    assert "Coordenador de Logística" in prompt
    assert "Guarulhos, SP, Brasil" in prompt
    assert "Presencial" in prompt
    assert "CLT" in prompt
    assert client.responses.last_kwargs["tools"] == [{"type": "web_search"}]
    assert result.median_salary == 10500
    assert result.salary_min == 10500
    assert result.salary_max == 10500
    assert result.currency == "BRL"


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        ("title", "Cargo"),
        ("location", "Cidade/Estado/País"),
        ("work_model", "Modelo"),
        ("employment_type", "Tipo"),
    ],
)
def test_research_requires_all_salary_context_fields(
    field: str,
    expected: str,
    tmp_path,
) -> None:
    values = {
        "title": "Analista",
        "location": "São Paulo, SP, Brasil",
        "work_model": "Híbrido",
        "employment_type": "CLT",
    }
    values[field] = ""
    service = SalaryResearchService(
        client=_Client({}),
        cache_path=tmp_path / "cache.json",
    )

    with pytest.raises(ValueError, match=expected):
        service.research(SalaryResearchRequest(**values))


def test_research_rejects_payload_without_median_salary(tmp_path) -> None:
    service = SalaryResearchService(
        client=_Client(
            {
                "salary_min": 15000,
                "salary_max": 10000,
                "currency": "BRL",
            }
        ),
        cache_path=tmp_path / "cache.json",
    )

    with pytest.raises(
        RuntimeError,
        match="não encontrou valores monetários comparáveis",
    ):
        service.research(
            SalaryResearchRequest(
                title="Gerente",
                location="Brasil",
                work_model="Remoto",
                employment_type="PJ",
            )
        )


def test_research_reuses_cache_for_equivalent_title_within_30_days(tmp_path) -> None:
    client = _Client(
        {
            "median_salary": 9000,
            "currency": "BRL",
            "period": "mensal",
        }
    )
    service = SalaryResearchService(
        client=client,
        cache_path=tmp_path / "salary_cache.json",
    )

    first = service.research(
        SalaryResearchRequest(
            title="Analista de Logística Sr.",
            location="Guarulhos, SP, Brasil",
            work_model="Híbrido",
            employment_type="CLT",
        )
    )
    second = service.research(
        SalaryResearchRequest(
            title="Analista Sênior de Logística",
            location="Guarulhos - SP, Brasil",
            work_model="Hibrido",
            employment_type="CLT",
        )
    )

    assert first == second
    assert client.responses.calls == 1
    assert (tmp_path / "salary_cache.json").exists()


def test_force_refresh_ignores_cached_salary(tmp_path) -> None:
    client = _Client(
        {
            "median_salary": 9000,
            "currency": "BRL",
            "period": "mensal",
        }
    )
    service = SalaryResearchService(
        client=client,
        cache_path=tmp_path / "salary_cache.json",
    )
    request = SalaryResearchRequest(
        title="Coordenador de Logística",
        location="Guarulhos, SP, Brasil",
        work_model="Presencial",
        employment_type="CLT",
    )

    service.research(request)
    service.research(request)
    service.research(request, force_refresh=True)

    assert client.responses.calls == 2



def test_concurrent_equivalent_requests_share_one_api_call(tmp_path) -> None:
    client = _Client(
        {
            "median_salary": 8500,
            "currency": "BRL",
            "period": "mensal",
        }
    )
    service = SalaryResearchService(
        client=client,
        cache_path=tmp_path / "salary_cache.json",
    )
    requests = [
        SalaryResearchRequest(
            title="Analista de Logística Sr.",
            location="Guarulhos, SP, Brasil",
            work_model="Híbrido",
            employment_type="CLT",
        ),
        SalaryResearchRequest(
            title="Analista Sênior de Logística",
            location="Guarulhos - SP, Brasil",
            work_model="Hibrido",
            employment_type="CLT",
        ),
        SalaryResearchRequest(
            title="Analista de Logística Senior",
            location="Guarulhos, SP, Brasil",
            work_model="Híbrido",
            employment_type="CLT",
        ),
    ]

    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(service.research, requests))

    assert client.responses.calls == 1
    assert all(result.median_salary == 8500 for result in results)
    assert all(result.salary_min == 8500 for result in results)
    assert all(result.salary_max == 8500 for result in results)
