"""Pesquisa da mediana salarial assistida por IA com cache local de 30 dias."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
import json
import logging
from pathlib import Path
import re
from statistics import median
from threading import Lock, RLock
from typing import Any
import unicodedata

from acd.infrastructure.ai.providers import AIProvider, SettingsConfiguredAIProvider
from acd.security.secret_provider import read_setting
from acd.services.settings_service import SettingsService

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class SalaryResearchRequest:
    """Dados usados para pesquisar remuneração comparável para uma vaga."""

    title: str
    location: str
    work_model: str
    employment_type: str
    company: str = ""


@dataclass(frozen=True, slots=True)
class SalaryResearchResult:
    """Mediana salarial mensal retornada pela pesquisa."""

    median_salary: float
    currency: str
    period: str = "mensal"

    @property
    def salary_min(self) -> float:
        """Compatibilidade temporária com consumidores do resultado em faixa."""
        return self.median_salary

    @property
    def salary_max(self) -> float:
        """Compatibilidade temporária com consumidores do resultado em faixa."""
        return self.median_salary


class SalaryResearchService:
    """Pesquisa fontes públicas e retorna somente a mediana salarial mensal."""

    SUPPORTED_CURRENCIES = {"BRL", "USD", "EUR", "GBP"}
    CACHE_TTL_DAYS = 30
    TARGET_SOURCES = (
        "Glassdoor",
        "Robert Half",
        "Portal Salário",
        "Salariômetro/FIPE",
        "Indeed",
    )

    def __init__(
        self,
        *,
        client: Any | None = None,
        ai_provider: AIProvider | None = None,
        model: str | None = None,
        settings_service: SettingsService | None = None,
        cache_path: Path | None = None,
    ) -> None:
        self._client = client
        self._settings_service = settings_service or SettingsService()
        self._ai_provider = ai_provider or SettingsConfiguredAIProvider(
            self._settings_service
        )
        self._model = model or read_setting(
            "ACD_SALARY_RESEARCH_MODEL", default="salary-research"
        )
        if cache_path is not None:
            self._cache_path = cache_path
        else:
            self._cache_path = self._settings_service.settings_path.with_name(
                "salary_research_cache.json"
            )
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
        """Retorne somente a mediana mensal, usando cache por até 30 dias."""
        self._validate_request(request)
        cache_key = self._cache_key(request)

        with self._lock_for_key(cache_key):
            if not force_refresh:
                cached = self._get_cached(cache_key)
                if cached is not None:
                    return cached

            prompt = self._build_prompt(request)
            raw_text = self._request_ai(prompt)
            result = self._result_from_raw_text(raw_text)

            if result is None:
                logger.warning(
                    "Pesquisa salarial sem valores utilizáveis na primeira tentativa: %s",
                    self._diagnostic_excerpt(raw_text),
                )
                recovery_prompt = self._build_recovery_prompt(request, raw_text)
                recovery_text = self._request_ai(recovery_prompt)
                result = self._result_from_raw_text(recovery_text)
                if result is None:
                    logger.warning(
                        "Pesquisa salarial sem valores utilizáveis após recuperação: %s",
                        self._diagnostic_excerpt(recovery_text),
                    )
                    raise RuntimeError(
                        "A pesquisa salarial não encontrou valores monetários "
                        "comparáveis nas fontes consultadas. Tente novamente mais tarde "
                        "ou revise cargo, localidade e tipo de contratação."
                    )

            self._store_cached(cache_key, result)
            return result

    def _request_ai(self, prompt: str) -> str:
        """Execute uma tentativa de pesquisa usando o roteamento universal de IA."""
        if self._client is not None:
            response = self._client.responses.create(
                model=self._model,
                tools=[{"type": "web_search"}],
                input=prompt,
            )
            return str(getattr(response, "output_text", "") or "")

        return self._ai_provider.generate_text(
            prompt=prompt,
            model="salary-research",
            temperature=0.0,
            max_tokens=1800,
            language="pt-BR",
            web_search=True,
        )

    def _result_from_raw_text(self, raw_text: str) -> SalaryResearchResult | None:
        """Converta JSON ou texto salarial livre em uma mediana determinística."""
        try:
            payload = self._parse_json(raw_text)
        except RuntimeError:
            payload = {}

        if payload:
            try:
                return self._normalize(payload)
            except RuntimeError as exc:
                if "moeda retornada" in str(exc):
                    raise

        text_values = self._extract_brl_values_from_text(raw_text)
        if not text_values:
            return None
        return SalaryResearchResult(
            median_salary=round(float(median(text_values)), 2),
            currency="BRL",
        )

    @classmethod
    def _build_recovery_prompt(
        cls,
        request: SalaryResearchRequest,
        previous_response: str,
    ) -> str:
        """Crie uma segunda consulta estrita quando a primeira não trouxer valores."""
        company = request.company.strip() or "não informada"
        sources = ", ".join(cls.TARGET_SOURCES)
        previous_excerpt = previous_response.strip()[:4000] or "(resposta vazia)"
        return f"""
Refaça a pesquisa salarial na web. A resposta anterior não continha valores
monetários utilizáveis pelo sistema.

Cargo: {request.title}
Empresa: {company}
Localidade: {request.location}
Modelo de trabalho: {request.work_model}
Tipo de contratação: {request.employment_type}

Consulte prioritariamente: {sources}.

Você DEVE retornar pelo menos um valor salarial mensal verificável se encontrar
dados públicos comparáveis. Não estime, não invente e não use anos, percentuais
ou contagens como salários. Converta valores anuais para mensal dividindo por 12.
Use no máximo um valor representativo por fonte.

Retorne SOMENTE este JSON, sem Markdown nem explicações:
{{
  "sources": [
    {{"name": "Nome da fonte", "value": 12500.00}}
  ],
  "currency": "BRL"
}}

Se nenhuma das fontes tiver valor salarial público comparável, retorne:
{{"sources": [], "currency": "BRL"}}

Resposta anterior, apenas para diagnóstico do que precisa ser corrigido:
{previous_excerpt}
""".strip()

    @classmethod
    def _extract_brl_values_from_text(cls, raw_text: str) -> list[float]:
        """Extraia apenas valores explicitamente monetários em reais de texto livre."""
        if not raw_text:
            return []

        matches = re.findall(
            r"(?i)(?:R\$|BRL)\s*([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]{1,2})?|"
            r"[0-9]{4,8}(?:[.,][0-9]{1,2})?)",
            raw_text,
        )
        values: list[float] = []
        for match in matches:
            value = cls._positive_float(match)
            if value is not None and 500 <= value <= 1_000_000:
                values.append(value)
        return values

    @staticmethod
    def _diagnostic_excerpt(raw_text: str) -> str:
        """Retorne trecho seguro e limitado para diagnóstico local."""
        text = re.sub(r"\s+", " ", raw_text or "").strip()
        return text[:2000] if text else "<resposta vazia>"

    def clear_cache(self) -> None:
        """Apague o cache salarial local."""
        with self._cache_lock:
            try:
                self._cache_path.unlink()
            except FileNotFoundError:
                return

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

    @classmethod
    def _build_prompt(cls, request: SalaryResearchRequest) -> str:
        company = request.company.strip() or "não informada"
        source_names = ", ".join(cls.TARGET_SOURCES)
        return f"""
Faça uma pesquisa salarial na web para a vaga abaixo e retorne SOMENTE a mediana
mensal dos valores válidos encontrados.

Cargo: {request.title}
Empresa: {company}
Localidade: {request.location}
Modelo de trabalho: {request.work_model}
Tipo de contratação: {request.employment_type}

Pesquise prioritariamente nestas fontes: {source_names}.
Para cada fonte, procure primeiro Cargo + Empresa + Cidade. Se não houver dado
comparável suficiente, use Cargo + Cidade; depois Cargo + Estado; por último Cargo + Brasil.

Regras obrigatórias:
- considere a senioridade contida no cargo;
- não misture regimes de contratação diferentes;
- leve em conta o modelo presencial, híbrido ou remoto quando houver dado disponível;
- normalize todos os valores para remuneração bruta mensal na mesma moeda;
- se a fonte trouxer valor anual, divida por 12;
- não invente valores nem fontes;
- ignore fontes sem valor salarial verificável e comparável;
- use no máximo um valor representativo por fonte para evitar duplicidade;
- retorne o valor mensal representativo de cada fonte encontrada;
- NÃO é necessário calcular a mediana; o ACD fará esse cálculo localmente;
- se uma fonte não tiver valor comparável, omita essa fonte;
- não retorne anos, percentuais, quantidade de vagas ou outros números como salário.

Retorne SOMENTE JSON válido, sem Markdown e sem explicações, preferencialmente:
{{
  "sources": [
    {{"name": "Glassdoor", "value": 0.0}},
    {{"name": "Robert Half", "value": 0.0}}
  ],
  "currency": "BRL"
}}

Também são aceitos, por compatibilidade, "values": [0.0] ou apenas
"median_salary": 0.0 quando a fonte consultada só informar uma mediana confiável.
""".strip()

    @staticmethod
    def _parse_json(raw_text: str) -> dict[str, Any]:
        """Extrai o primeiro objeto JSON válido, mesmo com texto/Markdown ao redor."""
        text = raw_text.strip()
        if not text:
            raise RuntimeError(
                "A IA não retornou valores salariais em formato válido."
            )

        fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if fenced:
            text = fenced.group(1).strip()

        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = SalaryResearchService._extract_json_object(text)

        if not isinstance(payload, dict):
            raise RuntimeError("A resposta da pesquisa salarial é inválida.")
        return payload

    @staticmethod
    def _extract_json_object(text: str) -> dict[str, Any]:
        decoder = json.JSONDecoder()
        for match in re.finditer(r"\{", text):
            try:
                candidate, _end = decoder.raw_decode(text[match.start() :])
            except json.JSONDecodeError:
                continue
            if isinstance(candidate, dict):
                return candidate
        raise RuntimeError(
            "A IA não retornou valores salariais em formato válido."
        )

    def _normalize(self, payload: dict[str, Any]) -> SalaryResearchResult:
        values = self._extract_salary_values(payload)
        reported = self._first_positive_value(
            payload,
            (
                "median_salary",
                "median",
                "salary",
                "monthly_salary",
                "remuneration",
                "value",
            ),
        )

        if values:
            # A IA pesquisa; o ACD calcula a mediana localmente para manter
            # o resultado determinístico e independente do provedor escolhido.
            median_salary = round(float(median(values)), 2)
        elif reported is not None:
            # Fallback seguro para fontes/respostas que forneçam apenas uma
            # mediana ou um único valor mensal confiável.
            median_salary = round(reported, 2)
        else:
            raise RuntimeError(
                "A IA não retornou valores salariais em formato válido."
            )

        currency = str(payload.get("currency", "BRL")).upper().strip()
        if currency in {"R$", "REAL", "REAIS"}:
            currency = "BRL"
        if currency not in self.SUPPORTED_CURRENCIES:
            raise RuntimeError(
                f"A moeda retornada ({currency}) não é suportada pelo aplicativo."
            )

        return SalaryResearchResult(
            median_salary=median_salary,
            currency=currency,
        )

    @classmethod
    def _extract_salary_values(cls, payload: dict[str, Any]) -> list[float]:
        values = cls._valid_values(payload.get("values"))
        if values:
            return values

        for collection_key in (
            "sources",
            "fontes",
            "results",
            "resultados",
            "salaries",
            "salarios",
        ):
            raw_collection = payload.get(collection_key)
            extracted = cls._values_from_collection(raw_collection)
            if extracted:
                return extracted

        return []

    @classmethod
    def _values_from_collection(cls, raw_collection: object) -> list[float]:
        if not isinstance(raw_collection, list):
            return []

        values: list[float] = []
        aliases = (
            "value",
            "salary",
            "monthly_salary",
            "median_salary",
            "remuneration",
            "valor",
            "salario",
            "salário",
            "remuneracao",
            "remuneração",
        )
        for item in raw_collection:
            if isinstance(item, dict):
                value = cls._first_positive_value(item, aliases)
            else:
                value = cls._positive_float(item)
            if value is not None:
                values.append(value)
        return values

    @classmethod
    def _first_positive_value(
        cls,
        payload: dict[str, Any],
        keys: tuple[str, ...],
    ) -> float | None:
        for key in keys:
            if key not in payload:
                continue
            value = cls._positive_float(payload.get(key))
            if value is not None:
                return value
        return None

    @staticmethod
    def _valid_values(raw_values: object) -> list[float]:
        if not isinstance(raw_values, list):
            return []
        values: list[float] = []
        for raw in raw_values:
            value = SalaryResearchService._positive_float(raw)
            if value is not None:
                values.append(value)
        return values

    @staticmethod
    def _positive_float(value: object) -> float | None:
        if isinstance(value, bool) or value is None:
            return None
        if isinstance(value, (int, float)):
            parsed = float(value)
            return parsed if parsed > 0 else None
        if not isinstance(value, str):
            return None

        text = value.strip()
        if not text:
            return None

        cleaned = re.sub(r"(?i)\b(?:BRL|R\$|USD|US\$|EUR|GBP)\b", "", text)
        cleaned = re.sub(r"[^0-9,.-]", "", cleaned)
        if not cleaned:
            return None

        if "," in cleaned and "." in cleaned:
            if cleaned.rfind(",") > cleaned.rfind("."):
                cleaned = cleaned.replace(".", "").replace(",", ".")
            else:
                cleaned = cleaned.replace(",", "")
        elif "," in cleaned:
            parts = cleaned.split(",")
            if len(parts) == 2 and len(parts[1]) in {1, 2}:
                cleaned = parts[0].replace(".", "") + "." + parts[1]
            else:
                cleaned = cleaned.replace(",", "")
        elif cleaned.count(".") > 1:
            cleaned = cleaned.replace(".", "")
        elif "." in cleaned:
            left, right = cleaned.rsplit(".", 1)
            if len(right) == 3 and left.replace("-", "").isdigit():
                cleaned = left + right

        try:
            parsed = float(cleaned)
        except ValueError:
            return None
        return parsed if parsed > 0 else None

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
                return self._normalize_cached(row)
            except RuntimeError:
                rows.pop(key, None)
                self._save_cache(rows)
                return None

    def _normalize_cached(self, payload: dict[str, Any]) -> SalaryResearchResult:
        median_salary = self._positive_float(payload.get("median_salary"))
        if median_salary is None:
            # Migração transparente de cache antigo em faixa: usa o ponto médio
            # somente para invalidar a dependência antiga sem quebrar a aplicação.
            salary_min = self._positive_float(payload.get("salary_min"))
            salary_max = self._positive_float(payload.get("salary_max"))
            if salary_min is None or salary_max is None:
                raise RuntimeError("Cache salarial antigo inválido.")
            median_salary = (salary_min + salary_max) / 2

        currency = str(payload.get("currency", "BRL")).upper().strip()
        if currency not in self.SUPPORTED_CURRENCIES:
            raise RuntimeError("Cache salarial com moeda inválida.")
        return SalaryResearchResult(round(median_salary, 2), currency)

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
            cls._normalize_text(request.company),
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
