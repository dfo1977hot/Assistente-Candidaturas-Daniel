from pathlib import Path

from acd.services.salary_research_service import (
    SalaryResearchRequest,
    SalaryResearchService,
)


class _Settings:
    settings_path = Path("settings.json")


class _AIProvider:
    def __init__(self, payload: str) -> None:
        self.payload = payload
        self.calls: list[dict[str, object]] = []

    def generate_text(self, **kwargs: object) -> str:
        self.calls.append(kwargs)
        return self.payload


def _service(tmp_path: Path, payload: str) -> tuple[SalaryResearchService, _AIProvider]:
    provider = _AIProvider(payload)
    service = SalaryResearchService(
        ai_provider=provider,
        settings_service=_Settings(),
        cache_path=tmp_path / "salary.json",
    )
    return service, provider


def test_salary_research_calculates_odd_median(tmp_path: Path) -> None:
    service, _provider = _service(
        tmp_path,
        '{"values":[11800,12300,12500,12900,14000],"median_salary":12500,"currency":"BRL"}',
    )
    result = service.research(
        SalaryResearchRequest(
            title="Coordenador de Logística",
            company="Empresa X",
            location="Guarulhos - SP",
            work_model="Presencial",
            employment_type="CLT",
        )
    )
    assert result.median_salary == 12500
    assert result.salary_min == 12500
    assert result.salary_max == 12500


def test_salary_research_calculates_even_median(tmp_path: Path) -> None:
    service, _provider = _service(
        tmp_path,
        '{"values":[10000,12000,14000,16000],"median_salary":13000,"currency":"BRL"}',
    )
    result = service.research(
        SalaryResearchRequest("Gerente", "São Paulo - SP", "Híbrido", "CLT")
    )
    assert result.median_salary == 13000


def test_salary_research_requires_web_search_and_named_sources(tmp_path: Path) -> None:
    service, provider = _service(
        tmp_path,
        '{"values":[12000],"median_salary":12000,"currency":"BRL"}',
    )
    service.research(
        SalaryResearchRequest(
            title="Analista",
            company="ACME",
            location="São Paulo - SP",
            work_model="Remoto",
            employment_type="CLT",
        )
    )
    call = provider.calls[0]
    assert call["web_search"] is True
    prompt = str(call["prompt"])
    for source in (
        "Glassdoor",
        "Robert Half",
        "Portal Salário",
        "Salariômetro/FIPE",
        "Indeed",
    ):
        assert source in prompt
    assert "Empresa: ACME" in prompt


def test_salary_research_ignores_incorrect_reported_median(tmp_path: Path) -> None:
    service, _provider = _service(
        tmp_path,
        '{"values":[10000,12000,14000],"median_salary":99999,"currency":"BRL"}',
    )
    request = SalaryResearchRequest("Analista", "São Paulo", "Híbrido", "CLT")

    result = service.research(request)

    assert result.median_salary == 12000


def test_salary_research_accepts_fenced_json(tmp_path: Path) -> None:
    service, _provider = _service(
        tmp_path,
        """```json
{\"values\":[10500,12000,13500,14000,16000],\"currency\":\"BRL\"}
```""",
    )

    result = service.research(
        SalaryResearchRequest("Analista", "São Paulo", "Híbrido", "CLT")
    )

    assert result.median_salary == 13500


def test_salary_research_accepts_json_surrounded_by_text(tmp_path: Path) -> None:
    service, _provider = _service(
        tmp_path,
        (
            "Valores localizados nas fontes consultadas:\n"
            '{"values":[10500,12000,13500,14000,16000],"currency":"BRL"}\n'
            "Pesquisa concluída."
        ),
    )

    result = service.research(
        SalaryResearchRequest("Analista", "São Paulo", "Híbrido", "CLT")
    )

    assert result.median_salary == 13500


def test_salary_research_accepts_sources_structure(tmp_path: Path) -> None:
    service, _provider = _service(
        tmp_path,
        """{
          "sources": [
            {"name": "Glassdoor", "value": 12500},
            {"name": "Indeed", "salary": 13200},
            {"name": "Portal Salário", "monthly_salary": 11950}
          ],
          "currency": "BRL"
        }""",
    )

    result = service.research(
        SalaryResearchRequest("Analista", "São Paulo", "Híbrido", "CLT")
    )

    assert result.median_salary == 12500


def test_salary_research_accepts_brazilian_currency_strings(tmp_path: Path) -> None:
    service, _provider = _service(
        tmp_path,
        """{
          "fontes": [
            {"nome": "Glassdoor", "valor": "R$ 12.500,00"},
            {"nome": "Indeed", "salário": "13.200,00"},
            {"nome": "Portal Salário", "remuneração": "R$ 11.950,00"}
          ],
          "currency": "R$"
        }""",
    )

    result = service.research(
        SalaryResearchRequest("Analista", "São Paulo", "Híbrido", "CLT")
    )

    assert result.median_salary == 12500
    assert result.currency == "BRL"


def test_salary_research_accepts_single_median_alias(tmp_path: Path) -> None:
    service, _provider = _service(
        tmp_path,
        '{"median": "R$ 14.750,00", "currency": "BRL"}',
    )

    result = service.research(
        SalaryResearchRequest("Especialista", "São Paulo", "Presencial", "CLT")
    )

    assert result.median_salary == 14750


def test_salary_research_rejects_payload_without_salary_values(tmp_path: Path) -> None:
    service, _provider = _service(
        tmp_path,
        '{"sources":[{"name":"Glassdoor","note":"sem dado"}],"currency":"BRL"}',
    )

    try:
        service.research(
            SalaryResearchRequest("Analista", "São Paulo", "Híbrido", "CLT")
        )
    except RuntimeError as exc:
        assert "valores monetários comparáveis" in str(exc)
    else:
        raise AssertionError("Era esperado erro para resposta sem valores salariais.")


class _SequenceAIProvider:
    def __init__(self, payloads: list[str]) -> None:
        self.payloads = list(payloads)
        self.calls: list[dict[str, object]] = []

    def generate_text(self, **kwargs: object) -> str:
        self.calls.append(kwargs)
        return self.payloads.pop(0)


def test_salary_research_recovers_with_second_strict_query(tmp_path: Path) -> None:
    provider = _SequenceAIProvider(
        [
            "Não encontrei dados em formato estruturado.",
            '{"sources":[{"name":"Glassdoor","value":12500},'
            '{"name":"Indeed","value":13500},'
            '{"name":"Portal Salário","value":13000}],"currency":"BRL"}',
        ]
    )
    service = SalaryResearchService(
        ai_provider=provider,  # type: ignore[arg-type]
        settings_service=_Settings(),
        cache_path=tmp_path / "salary.json",
    )

    result = service.research(
        SalaryResearchRequest("Analista", "São Paulo", "Híbrido", "CLT"),
        force_refresh=True,
    )

    assert result.median_salary == 13000
    assert len(provider.calls) == 2
    assert "Refaça a pesquisa salarial" in str(provider.calls[1]["prompt"])


def test_salary_research_extracts_brl_values_from_free_text(tmp_path: Path) -> None:
    service, _provider = _service(
        tmp_path,
        (
            "Glassdoor: R$ 12.500,00 por mês. "
            "Indeed: R$ 13.500,00 mensais. "
            "Portal Salário: BRL 13.000,00."
        ),
    )

    result = service.research(
        SalaryResearchRequest("Analista", "São Paulo", "Híbrido", "CLT"),
        force_refresh=True,
    )

    assert result.median_salary == 13000


def test_salary_research_raises_clear_error_after_two_empty_attempts(
    tmp_path: Path,
) -> None:
    provider = _SequenceAIProvider(
        [
            '{"sources":[],"currency":"BRL"}',
            '{"sources":[],"currency":"BRL"}',
        ]
    )
    service = SalaryResearchService(
        ai_provider=provider,  # type: ignore[arg-type]
        settings_service=_Settings(),
        cache_path=tmp_path / "salary.json",
    )

    try:
        service.research(
            SalaryResearchRequest("Analista", "São Paulo", "Híbrido", "CLT"),
            force_refresh=True,
        )
    except RuntimeError as exc:
        assert "não encontrou valores monetários comparáveis" in str(exc)
    else:
        raise AssertionError("Era esperado erro após duas tentativas sem valores.")

    assert len(provider.calls) == 2
