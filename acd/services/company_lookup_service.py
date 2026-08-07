from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
import json
import re
import socket
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from acd.security.secret_provider import EnvironmentSecretProvider, read_setting


class CompanyLookupError(RuntimeError):
    """Erro funcional ao consultar dados públicos de empresas."""


@dataclass(frozen=True, slots=True)
class CompanyLookupResult:
    name: str
    legal_name: str = ""
    tax_id: str = ""
    registration_status: str = ""
    segment: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    postal_code: str = ""
    country: str = ""
    phone: str = ""
    website: str = ""
    source: str = ""
    source_reference: str = ""
    confidence: float = 0.0
    retrieved_at: datetime | None = None


class CompanyLookupProvider(Protocol):
    def search(self, name: str, *, limit: int = 8) -> list[CompanyLookupResult]: ...


class OpenAIWebCompanyLookupProvider:
    """Pesquisa empresas com a OpenAI Responses API e busca web."""

    endpoint = "https://api.openai.com/v1/responses"

    _schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "companies": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "name": {"type": "string"},
                        "legal_name": {"type": "string"},
                        "tax_id": {"type": "string"},
                        "registration_status": {"type": "string"},
                        "segment": {"type": "string"},
                        "address": {"type": "string"},
                        "city": {"type": "string"},
                        "state": {"type": "string"},
                        "postal_code": {"type": "string"},
                        "country": {"type": "string"},
                        "phone": {"type": "string"},
                        "website": {"type": "string"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "sources": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": [
                        "name",
                        "legal_name",
                        "tax_id",
                        "registration_status",
                        "segment",
                        "address",
                        "city",
                        "state",
                        "postal_code",
                        "country",
                        "phone",
                        "website",
                        "confidence",
                        "sources",
                    ],
                },
            }
        },
        "required": ["companies"],
    }

    def __init__(
        self,
        api_key: str | None = None,
        *,
        model: str | None = None,
        timeout_seconds: float | None = None,
        client: Any | None = None,
    ) -> None:
        self.api_key = (api_key or EnvironmentSecretProvider().get_secret("OPENAI_API_KEY") or "").strip()
        self.model = (model or read_setting("OPENAI_COMPANY_LOOKUP_MODEL", default="gpt-5-mini")).strip()
        configured_timeout = read_setting("OPENAI_COMPANY_LOOKUP_TIMEOUT", default="120").strip()
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else _positive_float(configured_timeout, default=120.0)
        )
        self._client = client

    def search(self, name: str, *, limit: int = 8) -> list[CompanyLookupResult]:
        query = _validate_query(name)
        if not self.api_key and self._client is None:
            raise CompanyLookupError(
                "Configure OPENAI_API_KEY no ambiente para usar a busca assistida por IA."
            )

        prompt = (
            "Pesquise na web empresas que correspondam ao nome informado. "
            "Priorize a organização ou unidade no Brasil, sem inventar dados. "
            "Retorne somente informações verificáveis em fontes públicas. "
            "Quando um campo não puder ser confirmado, retorne string vazia. "
            "CNPJ deve conter apenas o valor encontrado na fonte, sem inferência. "
            f"Nome pesquisado: {query!r}. Máximo de resultados: {max(1, min(limit, 8))}."
        )

        try:
            response_payload = self._create_response(prompt)
            output_text = self._extract_output_text(response_payload)
            payload = json.loads(output_text)
        except CompanyLookupError:
            raise
        except json.JSONDecodeError as exc:
            raise CompanyLookupError(
                "A OpenAI respondeu, mas os dados da empresa vieram em formato inválido."
            ) from exc
        except Exception as exc:
            raise CompanyLookupError(_friendly_openai_error(exc)) from exc

        retrieved_at = datetime.now(UTC).replace(tzinfo=None)
        results: list[CompanyLookupResult] = []
        companies = payload.get("companies", [])
        if not isinstance(companies, list):
            raise CompanyLookupError(
                "A OpenAI respondeu, mas não retornou uma lista válida de empresas."
            )

        for item in companies[: max(1, min(limit, 8))]:
            if not isinstance(item, dict):
                continue
            company_name = str(item.get("name", "")).strip()
            if not company_name:
                continue
            raw_sources = item.get("sources", [])
            sources = (
                [str(value).strip() for value in raw_sources if str(value).strip()]
                if isinstance(raw_sources, list)
                else []
            )
            results.append(
                CompanyLookupResult(
                    name=company_name,
                    legal_name=str(item.get("legal_name", "")).strip(),
                    tax_id=str(item.get("tax_id", "")).strip(),
                    registration_status=str(item.get("registration_status", "")).strip(),
                    segment=str(item.get("segment", "")).strip(),
                    address=str(item.get("address", "")).strip(),
                    city=str(item.get("city", "")).strip(),
                    state=str(item.get("state", "")).strip(),
                    postal_code=str(item.get("postal_code", "")).strip(),
                    country=str(item.get("country", "")).strip(),
                    phone=str(item.get("phone", "")).strip(),
                    website=str(item.get("website", "")).strip(),
                    source="OpenAI com pesquisa web",
                    source_reference=" | ".join(sources[:5]),
                    confidence=_clamp_confidence(item.get("confidence", 0.0)),
                    retrieved_at=retrieved_at,
                )
            )
        return results

    def _create_response(self, prompt: str) -> dict[str, Any]:
        if self._client is not None:
            response = self._client.responses.create(
                model=self.model,
                tools=[{"type": "web_search"}],
                input=prompt,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "company_lookup_results",
                        "strict": True,
                        "schema": self._schema,
                    }
                },
                store=False,
            )
            if hasattr(response, "model_dump"):
                return dict(response.model_dump())
            if isinstance(response, dict):
                return response
            return {"output_text": getattr(response, "output_text", "")}

        body = {
            "model": self.model,
            "tools": [{"type": "web_search"}],
            "input": prompt,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "company_lookup_results",
                    "strict": True,
                    "schema": self._schema,
                }
            },
            "store": False,
        }
        payload = json.dumps(
            body,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        request = Request(
            self.endpoint,
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json",
                "User-Agent": "ACD/0.1",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310
                raw = response.read()
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise CompanyLookupError(
                self._friendly_http_error(exc.code, detail)
            ) from exc
        except TimeoutError as exc:
            raise CompanyLookupError(
                "A pesquisa da OpenAI excedeu o tempo limite. Tente novamente; "
                "consultas com pesquisa web podem levar mais de um minuto."
            ) from exc
        except URLError as exc:
            reason = getattr(exc, "reason", None)
            if isinstance(reason, (TimeoutError, socket.timeout)):
                raise CompanyLookupError(
                    "A pesquisa da OpenAI excedeu o tempo limite. Tente novamente; "
                    "consultas com pesquisa web podem levar mais de um minuto."
                ) from exc
            raise CompanyLookupError(
                "Não foi possível acessar a OpenAI API. Verifique sua conexão, "
                "proxy, antivírus ou certificado do Windows."
            ) from exc

        try:
            decoded = raw.decode("utf-8")
            response_payload = json.loads(decoded)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CompanyLookupError(
                "A OpenAI API retornou uma resposta que não pôde ser interpretada."
            ) from exc

        if not isinstance(response_payload, dict):
            raise CompanyLookupError("A OpenAI API retornou uma resposta inesperada.")
        return response_payload

    @staticmethod
    def _extract_output_text(payload: dict[str, Any]) -> str:
        direct = payload.get("output_text")
        if isinstance(direct, str) and direct.strip():
            return direct.strip()

        fragments: list[str] = []
        output = payload.get("output", [])
        if isinstance(output, list):
            for item in output:
                if not isinstance(item, dict):
                    continue
                content = item.get("content", [])
                if not isinstance(content, list):
                    continue
                for part in content:
                    if not isinstance(part, dict):
                        continue
                    text = part.get("text")
                    if isinstance(text, str) and text.strip():
                        fragments.append(text.strip())

        if fragments:
            return "\n".join(fragments)

        status = str(payload.get("status", "")).strip().lower()
        if status == "incomplete":
            details = payload.get("incomplete_details")
            reason = details.get("reason", "") if isinstance(details, dict) else ""
            raise CompanyLookupError(
                "A OpenAI não concluiu a pesquisa"
                + (f" ({reason})." if reason else ".")
            )
        raise CompanyLookupError("A OpenAI não retornou dados para a pesquisa.")

    @staticmethod
    def _friendly_http_error(status: int, detail: str) -> str:
        message, code = _parse_api_error(detail)
        normalized = f"{code} {message}".lower()
        if status == 401 or "invalid_api_key" in normalized:
            return "A OPENAI_API_KEY é inválida ou não foi reconhecida."
        if status == 403:
            return "A chave da OpenAI não possui permissão para esta operação."
        if status == 429:
            if "insufficient_quota" in normalized or "quota" in normalized:
                return "A conta da OpenAI API está sem créditos ou limite disponível."
            return "O limite temporário da OpenAI API foi atingido. Tente novamente mais tarde."
        if status == 400:
            if "invalid_json" in normalized or "unicode" in normalized:
                return "A OpenAI recusou a requisição por codificação inválida."
            if "model" in normalized:
                return "O modelo configurado para a busca não está disponível neste projeto."
            return message or "A OpenAI recusou os dados enviados para a pesquisa."
        if status >= 500:
            return "A OpenAI API está temporariamente indisponível."
        return message or f"A OpenAI API recusou a consulta (código {status})."


class ReceitaWSCompanyEnricher:
    """Confirma dados cadastrais brasileiros quando um CNPJ está disponível."""

    endpoint_template = "https://www.receitaws.com.br/v1/cnpj/{tax_id}"

    def __init__(self, *, timeout_seconds: float = 12.0) -> None:
        self.timeout_seconds = timeout_seconds

    def enrich(self, result: CompanyLookupResult) -> CompanyLookupResult:
        digits = _tax_id_digits(result.tax_id)
        if len(digits) != 14:
            return result
        request = Request(
            self.endpoint_template.format(tax_id=digits),
            headers={"Accept": "application/json", "User-Agent": "ACD/0.1"},
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError):
            return result
        if payload.get("status") == "ERROR":
            return result

        street = " ".join(
            part.strip()
            for part in (
                payload.get("logradouro", ""),
                payload.get("numero", ""),
                payload.get("complemento", ""),
                payload.get("bairro", ""),
            )
            if isinstance(part, str) and part.strip()
        )
        activity = ""
        activities = payload.get("atividade_principal") or []
        if activities and isinstance(activities[0], dict):
            activity = str(activities[0].get("text", "")).strip()

        source_reference = result.source_reference
        receita_reference = self.endpoint_template.format(tax_id=digits)
        if receita_reference not in source_reference:
            source_reference = " | ".join(part for part in (source_reference, receita_reference) if part)

        return replace(
            result,
            name=str(payload.get("fantasia") or result.name).strip(),
            legal_name=str(payload.get("nome") or result.legal_name).strip(),
            tax_id=str(payload.get("cnpj") or result.tax_id).strip(),
            registration_status=str(payload.get("situacao") or result.registration_status).strip(),
            segment=activity or result.segment,
            address=street or result.address,
            city=str(payload.get("municipio") or result.city).strip(),
            state=str(payload.get("uf") or result.state).strip(),
            postal_code=str(payload.get("cep") or result.postal_code).strip(),
            country="Brasil",
            phone=str(payload.get("telefone") or result.phone).strip(),
            source="OpenAI + ReceitaWS",
            source_reference=source_reference,
            confidence=max(result.confidence, 0.95),
        )


class GooglePlacesCompanyLookupProvider:
    """Consulta empresas pela API Places Text Search."""

    endpoint = "https://places.googleapis.com/v1/places:searchText"
    field_mask = ",".join(
        (
            "places.id",
            "places.displayName",
            "places.formattedAddress",
            "places.addressComponents",
            "places.primaryTypeDisplayName",
            "places.businessStatus",
            "places.internationalPhoneNumber",
            "places.nationalPhoneNumber",
            "places.websiteUri",
            "places.googleMapsUri",
        )
    )

    def __init__(self, api_key: str | None = None, *, timeout_seconds: float = 15.0) -> None:
        self.api_key = (api_key or read_setting("GOOGLE_PLACES_API_KEY")).strip()
        self.timeout_seconds = timeout_seconds

    def search(self, name: str, *, limit: int = 8) -> list[CompanyLookupResult]:
        query = _validate_query(name)
        if not self.api_key:
            raise CompanyLookupError(
                "Configure GOOGLE_PLACES_API_KEY no ambiente para usar o Google Places."
            )
        payload = json.dumps(
            {
                "textQuery": query,
                "pageSize": max(1, min(limit, 20)),
                "languageCode": "pt-BR",
                "regionCode": "BR",
            }
        ).encode("utf-8")
        request = Request(
            self.endpoint,
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.api_key,
                "X-Goog-FieldMask": self.field_mask,
            },
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise CompanyLookupError(self._friendly_http_error(exc.code, detail)) from exc
        except (URLError, TimeoutError) as exc:
            raise CompanyLookupError(
                "Não foi possível acessar o Google Places. Verifique sua conexão."
            ) from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CompanyLookupError("O Google Places retornou uma resposta inválida.") from exc
        return [
            self._parse_place(place)
            for place in body.get("places", [])
            if place.get("displayName", {}).get("text")
        ]

    @staticmethod
    def _friendly_http_error(status: int, detail: str) -> str:
        del detail
        if status in {401, 403}:
            return "A chave do Google Places é inválida, está sem permissão ou sem faturamento habilitado."
        if status == 429:
            return "O limite temporário de consultas do Google foi atingido."
        if status == 400:
            return "A consulta foi recusada pelo Google. Revise a configuração da API."
        return f"O Google Places está indisponível no momento (código {status})."

    @classmethod
    def _parse_place(cls, place: dict[str, Any]) -> CompanyLookupResult:
        components = place.get("addressComponents") or []
        by_type: dict[str, str] = {}
        short_by_type: dict[str, str] = {}
        for component in components:
            for component_type in component.get("types", []):
                by_type.setdefault(component_type, component.get("longText", ""))
                short_by_type.setdefault(component_type, component.get("shortText", ""))
        city = (
            by_type.get("locality")
            or by_type.get("administrative_area_level_2")
            or by_type.get("sublocality")
            or ""
        )
        state = short_by_type.get("administrative_area_level_1") or by_type.get(
            "administrative_area_level_1", ""
        )
        return CompanyLookupResult(
            name=place["displayName"]["text"].strip(),
            registration_status=place.get("businessStatus", "").replace("_", " ").title(),
            segment=(place.get("primaryTypeDisplayName") or {}).get("text", ""),
            address=place.get("formattedAddress", "").strip(),
            city=city.strip(),
            state=state.strip(),
            postal_code=by_type.get("postal_code", "").strip(),
            country=by_type.get("country", "").strip(),
            phone=(
                place.get("internationalPhoneNumber")
                or place.get("nationalPhoneNumber")
                or ""
            ).strip(),
            website=place.get("websiteUri", "").strip(),
            source="Google Places",
            source_reference=(place.get("googleMapsUri") or place.get("id") or "").strip(),
            confidence=0.75,
            retrieved_at=datetime.now(UTC).replace(tzinfo=None),
        )


class HybridCompanyLookupProvider:
    """OpenAI como fonte principal, ReceitaWS para confirmação e Google como contingência."""

    def __init__(
        self,
        openai_provider: CompanyLookupProvider | None = None,
        receita_enricher: ReceitaWSCompanyEnricher | None = None,
        google_provider: CompanyLookupProvider | None = None,
    ) -> None:
        self.openai_provider = openai_provider or OpenAIWebCompanyLookupProvider()
        self.receita_enricher = receita_enricher or ReceitaWSCompanyEnricher()
        self.google_provider = google_provider or GooglePlacesCompanyLookupProvider()

    def search(self, name: str, *, limit: int = 8) -> list[CompanyLookupResult]:
        primary_error: CompanyLookupError | None = None
        try:
            primary = self.openai_provider.search(name, limit=limit)
            if primary:
                return [self.receita_enricher.enrich(result) for result in primary]
        except CompanyLookupError as exc:
            primary_error = exc

        try:
            return self.google_provider.search(name, limit=limit)
        except CompanyLookupError as fallback_error:
            if primary_error:
                raise CompanyLookupError(
                    f"Busca por IA: {primary_error}\nGoogle Places: {fallback_error}"
                ) from fallback_error
            raise


class CompanyLookupService:

    def __init__(
        self,
        provider: CompanyLookupProvider | None = None,
        *,
        provider_name: str | None = None,
        cache_ttl: timedelta = timedelta(hours=24),
    ) -> None:
        self.provider_name = _normalize_provider_name(
            provider_name or read_setting("COMPANY_LOOKUP_PROVIDER", default="hybrid")
        )
        self.provider = provider or self._build_provider(self.provider_name)
        self.cache_ttl = cache_ttl
        self._cache: dict[tuple[str, str], tuple[datetime, list[CompanyLookupResult]]] = {}

    @staticmethod
    def _build_provider(provider_name: str) -> CompanyLookupProvider:
        if provider_name == "openai":
            return OpenAIWebCompanyLookupProvider()
        if provider_name == "google":
            return GooglePlacesCompanyLookupProvider()
        return HybridCompanyLookupProvider()

    def search(self, name: str, *, force_refresh: bool = False) -> list[CompanyLookupResult]:
        query = _validate_query(name)
        key = (self.provider_name, query.casefold())
        cached = self._cache.get(key)
        now = datetime.now(UTC).replace(tzinfo=None)
        if not force_refresh and cached and now - cached[0] <= self.cache_ttl:
            return list(cached[1])
        results = self.provider.search(query, limit=8)
        self._cache[key] = (now, list(results))
        return results


def _positive_float(value: str, *, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _validate_query(name: str) -> str:
    query = name.strip()
    if len(query) < 2:
        raise ValueError("Informe pelo menos dois caracteres do nome da empresa.")
    return query


def _normalize_provider_name(value: str) -> str:
    normalized = value.strip().lower()
    aliases = {
        "híbrida": "hybrid",
        "hibrida": "hybrid",
        "openai + receitaws": "hybrid",
        "ia": "openai",
        "google places": "google",
    }
    normalized = aliases.get(normalized, normalized)
    return normalized if normalized in {"hybrid", "openai", "google"} else "hybrid"


def _tax_id_digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def _clamp_confidence(value: Any) -> float:
    try:
        return max(0.0, min(float(value), 1.0))
    except (TypeError, ValueError):
        return 0.0


def _parse_api_error(detail: str) -> tuple[str, str]:
    try:
        payload = json.loads(detail)
    except json.JSONDecodeError:
        return detail.strip(), ""
    error = payload.get("error", {})
    if not isinstance(error, dict):
        return detail.strip(), ""
    return str(error.get("message", "")).strip(), str(error.get("code", "")).strip()


def _friendly_openai_error(exc: Exception) -> str:
    text = str(exc).lower()
    if "api key" in text or "authentication" in text or "401" in text:
        return "A OPENAI_API_KEY é inválida ou não foi reconhecida."
    if "insufficient_quota" in text or "billing" in text or "quota" in text:
        return "A conta da OpenAI API está sem créditos ou limite disponível."
    if "rate" in text or "429" in text:
        return "O limite temporário da OpenAI API foi atingido. Tente novamente mais tarde."
    if "timeout" in text:
        return "A consulta à OpenAI demorou além do limite. Tente novamente."
    return "Não foi possível concluir a busca pela OpenAI API."
