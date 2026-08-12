"""Pesquisa salarial assistida por IA com cache local de 30 dias."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import re
from threading import Lock, RLock
from typing import TYPE_CHECKING, Any
import unicodedata

from acd.security.secret_provider import EnvironmentSecretProvider, read_setting
from acd.services.settings_service import SettingsService

if TYPE_CHECKING:
    from openai import OpenAI


@dataclass(frozen=True, slots=True)
class SalaryResearchRequest:
    """Dados usados para pesquisar uma faixa salarial comparável."""

    title: str
    location: str
    work_model: str
    employment_type: str


@dataclass(frozen=True, slots=True)
class SalaryResearchResult:
    """Faixa salarial mensal retornada pela pesquisa."""

    salary_min: float
    salary_max: float
    currency: str
    period: str = "mensal"
    confidence: str = ""
    geographic_scope: str = ""
    summary: str = ""
    sources: tuple[str, ...] = ()


class SalaryResearchService:
    """Consulta a web somente quando o cache local não possui faixa recente."""

    SUPPORTED_CURRENCIES = {"BRL", "USD", "EUR", "GBP"}
    CACHE_TTL_DAYS = 30

    def __init__(
        self,
        *,
        client: OpenAI | None = None,
        model: str | None = None,
        settings_service: SettingsService | None = None,
        cache_path: Path | None = None,
    ) -> None:
        self._client = client
        self._settings_service = settings_service
        self._model = model or read_setting(
            "ACD_SALARY_RESEARCH_MODEL", default="gpt-5-mini"
        )
        if cache_path is not None:
            self._cache_path = cache_path
        elif settings_service is not None:
            self._cache_path = settings_service.settings_path.with_name(
                "salary_research_cache.json"
            )
        else:
            self._cache_path = Path.home() / ".acd" / "salary_research_cache.json"
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._cache_lock = RLock()
        self._key_locks_guard = Lock()
        self._key_locks: dict[str, RLock] = {}

    def research(
        self,
        request: SalaryResearchRequest,
        *,
        force_refresh: bool = False,
    ) -> SalaryResearchResult:
        """Retorne a faixa mensal; use cache salvo por 30 dias quando possível."""
        self._validate_request(request)
        cache_key = self._cache_key(request)

        with self._lock_for_key(cache_key):
            if not force_refresh:
                cached = self._get_cached(cache_key)
                if cached is not None:
                    return cached

            client = self._client or self._create_default_client()
            response = client.responses.create(
                model=self._model,
                tools=[{"type": "web_search"}],
                input=self._build_prompt(request),
            )
            result = self._normalize(self._parse_json(response.output_text))
            self._store_cached(cache_key, result)
            return result

    def clear_cache(self) -> None:
        """Apague o cache salarial local."""
        with self._cache_lock:
            try:
                self._cache_path.unlink()
            except FileNotFoundError:
                return

    def _create_default_client(self) -> Any:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "A biblioteca openai não está instalada no ambiente do aplicativo."
            ) from exc

        api_key = ""
        if self._settings_service is not None:
            api_key = self._settings_service.get_api_key("openai")
        if not api_key:
            api_key = EnvironmentSecretProvider().get_secret("OPENAI_API_KEY") or ""
        if not api_key:
            raise RuntimeError(
                "Configure a chave da OpenAI na página Configurações."
            )
        return OpenAI(api_key=api_key)

    @staticmethod
    def _validate_request(request: SalaryResearchRequest) -> None:
        missing = []
        if not request.title.strip():
            missing.append("Cargo")
        if not request.location.strip():
            missing.append("Cidade/Estado/País")
        if not request.work_model.strip():
            missing.append("Modelo")
        if not request.employment_type.strip():
            missing.append("Tipo")
        if missing:
            raise ValueError(
                "Preencha antes da pesquisa: " + ", ".join(missing) + "."
            )

    @staticmethod
    def _build_prompt(request: SalaryResearchRequest) -> str:
        return f"""
Pesquise na web uma faixa salarial mensal recente e comparável para esta vaga.

Cargo: {request.title}
Localidade: {request.location}
Modelo de trabalho: {request.work_model}
Tipo de contratação: {request.employment_type}

Use obrigatoriamente Cargo, Localidade, Modelo e Tipo.
Priorize a cidade; se não houver dados suficientes, amplie para Estado e depois País.
Não misture regimes de contratação nem senioridades.
Para dados anuais, converta para valor mensal dividindo por 12.
Use a moeda predominante da localidade.

Retorne SOMENTE JSON válido e sem explicações:
{{
  "salary_min": 0.0,
  "salary_max": 0.0,
  "currency": "BRL"
}}
""".strip()

    @staticmethod
    def _parse_json(raw_text: str) -> dict[str, Any]:
        text = raw_text.strip()
        fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if fenced:
            text = fenced.group(1)
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "A IA não retornou uma faixa salarial em formato válido."
            ) from exc
        if not isinstance(payload, dict):
            raise RuntimeError("A resposta da pesquisa salarial é inválida.")
        return payload

    def _normalize(self, payload: dict[str, Any]) -> SalaryResearchResult:
        try:
            salary_min = float(payload["salary_min"])
            salary_max = float(payload["salary_max"])
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError("A resposta não contém uma faixa salarial válida.") from exc

        if salary_min <= 0 or salary_max <= 0 or salary_min > salary_max:
            raise RuntimeError("A faixa salarial encontrada é inconsistente.")

        currency = str(payload.get("currency", "BRL")).upper().strip()
        if currency not in self.SUPPORTED_CURRENCIES:
            raise RuntimeError(
                f"A moeda retornada ({currency}) não é suportada pelo aplicativo."
            )

        return SalaryResearchResult(
            salary_min=round(salary_min, 2),
            salary_max=round(salary_max, 2),
            currency=currency,
        )

    def _lock_for_key(self, key: str) -> RLock:
        with self._key_locks_guard:
            return self._key_locks.setdefault(key, RLock())

    def _get_cached(self, key: str) -> SalaryResearchResult | None:
        with self._cache_lock:
            rows = self._load_cache()
            row = rows.get(key)
            if not isinstance(row, dict):
                return None
            timestamp = self._parse_timestamp(row.get("researched_at"))
            if timestamp is None:
                return None
            if datetime.now(UTC) - timestamp > timedelta(days=self.CACHE_TTL_DAYS):
                rows.pop(key, None)
                self._save_cache(rows)
                return None
            try:
                return self._normalize(row)
            except RuntimeError:
                rows.pop(key, None)
                self._save_cache(rows)
                return None

    def _store_cached(self, key: str, result: SalaryResearchResult) -> None:
        with self._cache_lock:
            rows = self._load_cache()
            row = asdict(result)
            row["researched_at"] = datetime.now(UTC).isoformat()
            rows[key] = row
            self._save_cache(rows)

    def _load_cache(self) -> dict[str, Any]:
        if not self._cache_path.exists():
            return {}
        try:
            payload = json.loads(self._cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def _save_cache(self, payload: dict[str, Any]) -> None:
        temporary = self._cache_path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(self._cache_path)

    @classmethod
    def _cache_key(cls, request: SalaryResearchRequest) -> str:
        parts = (
            cls._normalize_title(request.title),
            cls._normalize_text(request.location),
            cls._normalize_text(request.work_model),
            cls._normalize_text(request.employment_type),
        )
        return "|".join(parts)

    @classmethod
    def _normalize_title(cls, value: str) -> str:
        normalized = cls._normalize_text(value)
        replacements = (
            (r"\bsr\b", "senior"),
            (r"\bsenior\b", "senior"),
            (r"\bjr\b", "junior"),
            (r"\bjunior\b", "junior"),
            (r"\bpl\b", "pleno"),
        )
        for pattern, replacement in replacements:
            normalized = re.sub(pattern, replacement, normalized)
        words = normalized.split()
        stopwords = {"de", "da", "do", "das", "dos"}
        content = [word for word in words if word not in stopwords]
        seniority = [
            word for word in content if word in {"junior", "pleno", "senior"}
        ]
        role = [
            word for word in content if word not in {"junior", "pleno", "senior"}
        ]
        return " ".join(role + seniority)

    @staticmethod
    def _normalize_text(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value.casefold())
        ascii_value = normalized.encode("ascii", "ignore").decode()
        return re.sub(r"[^a-z0-9]+", " ", ascii_value).strip()

    @staticmethod
    def _parse_timestamp(value: object) -> datetime | None:
        if not isinstance(value, str) or not value:
            return None
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
