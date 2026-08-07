from __future__ import annotations

import json

import pytest

from acd.services.company_lookup_service import (
    CompanyLookupError,
    CompanyLookupResult,
    CompanyLookupService,
    HybridCompanyLookupProvider,
    OpenAIWebCompanyLookupProvider,
)


class _Response:
    def __init__(self, payload: dict) -> None:
        self.output_text = json.dumps(payload)


class _Responses:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return _Response(self.payload)


class _Client:
    def __init__(self, payload: dict) -> None:
        self.responses = _Responses(payload)


def test_openai_provider_requires_api_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    provider = OpenAIWebCompanyLookupProvider(api_key="")

    with pytest.raises(CompanyLookupError, match="OPENAI_API_KEY"):
        provider.search("Acme")


def test_openai_provider_parses_structured_result() -> None:
    client = _Client(
        {
            "companies": [
                {
                    "name": "Acme Brasil",
                    "legal_name": "Acme Brasil Ltda.",
                    "tax_id": "12.345.678/0001-90",
                    "registration_status": "ATIVA",
                    "segment": "Tecnologia",
                    "address": "Av. Paulista, 1000",
                    "city": "São Paulo",
                    "state": "SP",
                    "postal_code": "01310-100",
                    "country": "Brasil",
                    "phone": "(11) 1234-5678",
                    "website": "https://acme.example",
                    "confidence": 0.91,
                    "sources": ["https://acme.example/sobre"],
                }
            ]
        }
    )
    provider = OpenAIWebCompanyLookupProvider(client=client)

    results = provider.search("Acme")

    assert results[0].legal_name == "Acme Brasil Ltda."
    assert results[0].confidence == 0.91
    assert results[0].source == "OpenAI com pesquisa web"
    assert "web_search" in str(client.responses.kwargs["tools"])
    assert client.responses.kwargs["store"] is False


def test_hybrid_enriches_openai_results() -> None:
    original = CompanyLookupResult(name="Acme", tax_id="12345678000190")

    class Primary:
        def search(self, name: str, *, limit: int = 8):
            return [original]

    class Enricher:
        def enrich(self, result: CompanyLookupResult):
            return CompanyLookupResult(name=result.name, legal_name="Acme Ltda.")

    class Fallback:
        def search(self, name: str, *, limit: int = 8):
            raise AssertionError("fallback não deveria ser usado")

    provider = HybridCompanyLookupProvider(Primary(), Enricher(), Fallback())

    assert provider.search("Acme")[0].legal_name == "Acme Ltda."


def test_hybrid_uses_google_when_openai_fails() -> None:
    expected = [CompanyLookupResult(name="Acme Google")]

    class Primary:
        def search(self, name: str, *, limit: int = 8):
            raise CompanyLookupError("OpenAI indisponível")

    class Fallback:
        def search(self, name: str, *, limit: int = 8):
            return expected

    provider = HybridCompanyLookupProvider(Primary(), google_provider=Fallback())

    assert provider.search("Acme") == expected


def test_service_caches_results() -> None:
    calls = 0

    class Provider:
        def search(self, name: str, *, limit: int = 8):
            nonlocal calls
            calls += 1
            return [CompanyLookupResult(name=name)]

    service = CompanyLookupService(Provider(), provider_name="openai")

    service.search("Acme")
    service.search("Acme")

    assert calls == 1
