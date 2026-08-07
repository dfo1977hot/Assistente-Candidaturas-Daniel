from datetime import datetime
import json
from urllib.error import HTTPError

import pytest

import acd.services.company_lookup_service as lookup_module
from acd.services.company_lookup_service import (
    CompanyLookupError,
    CompanyLookupResult,
    CompanyLookupService,
    GooglePlacesCompanyLookupProvider,
    OpenAIWebCompanyLookupProvider,
)


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return self._body


def test_parse_google_place() -> None:
    result = GooglePlacesCompanyLookupProvider._parse_place({
        "id": "place-1",
        "displayName": {"text": "Acme Brasil"},
        "formattedAddress": "Av. Paulista, São Paulo - SP, 01310-100, Brasil",
        "addressComponents": [
            {"longText": "São Paulo", "shortText": "São Paulo", "types": ["locality"]},
            {
                "longText": "São Paulo",
                "shortText": "SP",
                "types": ["administrative_area_level_1"],
            },
            {
                "longText": "01310-100",
                "shortText": "01310-100",
                "types": ["postal_code"],
            },
            {"longText": "Brasil", "shortText": "BR", "types": ["country"]},
        ],
        "websiteUri": "https://acme.example",
        "nationalPhoneNumber": "(11) 1234-5678",
        "businessStatus": "OPERATIONAL",
        "primaryTypeDisplayName": {"text": "Empresa"},
    })
    assert result.name == "Acme Brasil"
    assert result.city == "São Paulo"
    assert result.state == "SP"
    assert result.postal_code == "01310-100"
    assert result.website == "https://acme.example"
    assert isinstance(result.retrieved_at, datetime)


def test_lookup_requires_google_api_key(monkeypatch) -> None:
    monkeypatch.delenv("GOOGLE_PLACES_API_KEY", raising=False)
    provider = GooglePlacesCompanyLookupProvider(api_key="")
    with pytest.raises(RuntimeError, match="GOOGLE_PLACES_API_KEY"):
        provider.search("Acme")


def test_service_delegates_to_provider() -> None:
    expected = [CompanyLookupResult(name="Acme")]

    class Provider:
        def search(self, name: str, *, limit: int = 8):
            assert name == "Acme" and limit == 8
            return expected

    assert CompanyLookupService(Provider()).search("Acme") == expected


def test_openai_request_is_utf8_and_parses_accented_result(monkeypatch) -> None:
    captured: dict[str, object] = {}
    structured = {
        "companies": [
            {
                "name": "Volkswagen do Brasil",
                "legal_name": "Volkswagen do Brasil Indústria de Veículos Automotores Ltda.",
                "tax_id": "",
                "registration_status": "",
                "segment": "Indústria automobilística",
                "address": "São Bernardo do Campo",
                "city": "São Bernardo do Campo",
                "state": "SP",
                "postal_code": "",
                "country": "Brasil",
                "phone": "",
                "website": "https://www.vw.com.br/",
                "confidence": 0.9,
                "sources": ["https://www.vw.com.br/"],
            }
        ]
    }
    api_payload = {
        "status": "completed",
        "output": [
            {
                "type": "message",
                "content": [
                    {
                        "type": "output_text",
                        "text": json.dumps(structured, ensure_ascii=False),
                    }
                ],
            }
        ],
    }

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return _FakeResponse(api_payload)

    monkeypatch.setattr(lookup_module, "urlopen", fake_urlopen)
    provider = OpenAIWebCompanyLookupProvider(api_key="sk-test")

    results = provider.search("Volkswagen", limit=3)

    request = captured["request"]
    assert request.headers["Content-type"] == "application/json; charset=utf-8"
    decoded_body = request.data.decode("utf-8")
    assert "organização" in decoded_body
    assert results[0].city == "São Bernardo do Campo"
    assert results[0].segment == "Indústria automobilística"


def test_openai_extracts_text_from_multiple_output_parts() -> None:
    payload = {
        "output": [
            {"content": [{"type": "output_text", "text": '{"companies":'}]},
            {"content": [{"type": "output_text", "text": "[]}"}]},
        ]
    }

    assert (
        OpenAIWebCompanyLookupProvider._extract_output_text(payload)
        == '{"companies":\n[]}'
    )


def test_openai_http_error_exposes_functional_reason(monkeypatch) -> None:
    error_body = json.dumps({
        "error": {
            "message": "Incorrect API key provided.",
            "type": "invalid_request_error",
            "code": "invalid_api_key",
        }
    }).encode("utf-8")

    def fake_urlopen(request, timeout):
        raise HTTPError(
            request.full_url,
            401,
            "Unauthorized",
            hdrs=None,
            fp=__import__("io").BytesIO(error_body),
        )

    monkeypatch.setattr(lookup_module, "urlopen", fake_urlopen)
    provider = OpenAIWebCompanyLookupProvider(api_key="sk-invalid")

    with pytest.raises(CompanyLookupError, match="OPENAI_API_KEY é inválida"):
        provider.search("Volkswagen")

def test_openai_default_timeout_is_suitable_for_web_search(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_COMPANY_LOOKUP_TIMEOUT", raising=False)

    provider = OpenAIWebCompanyLookupProvider(api_key="sk-test")

    assert provider.timeout_seconds == 120.0


def test_openai_timeout_can_be_configured(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_COMPANY_LOOKUP_TIMEOUT", "180")

    provider = OpenAIWebCompanyLookupProvider(api_key="sk-test")

    assert provider.timeout_seconds == 180.0


def test_openai_timeout_has_specific_functional_message(monkeypatch) -> None:

    def fake_urlopen(request, timeout):
        raise TimeoutError("timed out")

    monkeypatch.setattr(lookup_module, "urlopen", fake_urlopen)
    provider = OpenAIWebCompanyLookupProvider(api_key="sk-test", timeout_seconds=1)

    with pytest.raises(CompanyLookupError, match="excedeu o tempo limite"):
        provider.search("Volkswagen")



def test_service_force_refresh_bypasses_cache() -> None:
    calls = 0

    class Provider:
        def search(self, name: str, *, limit: int = 8):
            nonlocal calls
            calls += 1
            return [CompanyLookupResult(name=f"{name}-{calls}")]

    service = CompanyLookupService(Provider(), provider_name="openai")

    first = service.search("Acme")
    cached = service.search("Acme")
    refreshed = service.search("Acme", force_refresh=True)

    assert first[0].name == "Acme-1"
    assert cached[0].name == "Acme-1"
    assert refreshed[0].name == "Acme-2"
    assert calls == 2
