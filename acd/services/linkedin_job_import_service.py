from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any
from urllib.parse import urlparse

from acd.infrastructure.ai.providers import AIProvider, SettingsConfiguredAIProvider
from acd.security.secret_provider import read_setting
from acd.services.closed_linkedin_jobs_registry import ClosedLinkedInJobsRegistry
from acd.services.settings_service import SettingsService


class LinkedInJobImportError(RuntimeError):
    """Erro controlado durante a importação de uma vaga do LinkedIn."""


@dataclass(frozen=True, slots=True)
class ImportedLinkedInJob:
    """Dados estruturados extraídos de uma vaga do LinkedIn."""

    title: str = ""
    company_name: str = ""
    location: str = ""
    work_model: str = ""
    employment_type: str = ""
    salary_min: float | None = None
    salary_max: float | None = None
    currency: str = "BRL"
    recruiter: str = ""
    published_at: str = ""
    application_deadline: str = ""
    description: str = ""
    requirements: tuple[str, ...] = ()
    responsibilities: tuple[str, ...] = ()
    benefits: tuple[str, ...] = ()
    source_url: str = ""
    linkedin_job_id: str = ""
    confidence: str = ""
    source_references: tuple[str, ...] = ()
    accepting_applications: bool | None = None

    def notes_text(self) -> str:
        """Consolida o conteúdo detalhado para o campo Observações."""

        sections: list[str] = []
        if self.company_name:
            sections.append(f"Empresa identificada: {self.company_name}")
        if self.published_at:
            sections.append(f"Publicada em: {self.published_at}")
        if self.linkedin_job_id:
            sections.append(f"ID LinkedIn: {self.linkedin_job_id}")
        if self.confidence:
            sections.append(f"Confiança da importação: {self.confidence}")
        if self.description:
            sections.append(f"Descrição\n{self.description}")
        if self.responsibilities:
            sections.append(
                "Responsabilidades\n" + "\n".join(f"• {item}" for item in self.responsibilities)
            )
        if self.requirements:
            sections.append(
                "Requisitos\n" + "\n".join(f"• {item}" for item in self.requirements)
            )
        if self.benefits:
            sections.append("Benefícios\n" + "\n".join(f"• {item}" for item in self.benefits))
        if self.source_references:
            sections.append("Fontes\n" + "\n".join(self.source_references))
        return "\n\n".join(sections)


class LinkedInJobImportService:
    """Importa dados públicos de uma vaga usando a ordem global de IA."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
        closed_jobs_registry: ClosedLinkedInJobsRegistry | None = None,
        settings_service: SettingsService | None = None,
        ai_provider: AIProvider | None = None,
    ) -> None:
        self._api_key = (api_key or "").strip()
        self._settings_service = settings_service or SettingsService()
        self._ai_provider = ai_provider or SettingsConfiguredAIProvider(
            self._settings_service
        )
        self._closed_jobs_registry = (
            closed_jobs_registry or ClosedLinkedInJobsRegistry()
        )
        self._model = (model or read_setting("OPENAI_JOB_IMPORT_MODEL", default="gpt-5-mini")).strip()
        configured_timeout = read_setting("OPENAI_JOB_IMPORT_TIMEOUT", default="120")
        self._timeout = timeout if timeout is not None else self._parse_timeout(configured_timeout)

    def import_from_url(self, url: str) -> ImportedLinkedInJob:
        """Obtém e estrutura os dados públicos disponíveis para a URL informada."""

        normalized_url = self.normalize_linkedin_job_url(url)
        linkedin_job_id = self._closed_jobs_registry.job_id_from_url(normalized_url)
        if linkedin_job_id and self._closed_jobs_registry.contains(linkedin_job_id):
            return ImportedLinkedInJob(
                source_url=normalized_url,
                linkedin_job_id=linkedin_job_id,
                accepting_applications=False,
            )

        try:
            output_text = self._ai_provider.generate_text(
                prompt=self._build_prompt(normalized_url),
                model="linkedin-job-import",
                temperature=0.0,
                max_tokens=5000,
                language="pt-BR",
            )
        except Exception as exc:
            raise LinkedInJobImportError(
                f"Nenhum provedor de IA conseguiu importar a vaga: {exc}"
            ) from exc
        structured_data = self._parse_structured_json(output_text)
        result = self._to_result(structured_data, normalized_url)
        if result.accepting_applications is False:
            closed_id = (
                result.linkedin_job_id
                or self._closed_jobs_registry.job_id_from_url(normalized_url)
            )
            self._closed_jobs_registry.mark_closed(closed_id)
        return result

    @staticmethod
    def normalize_linkedin_job_url(url: str) -> str:
        """Valida e normaliza uma URL de vaga do LinkedIn."""

        candidate = url.strip()
        if not candidate:
            raise LinkedInJobImportError("Cole a URL da vaga do LinkedIn.")

        parsed = urlparse(candidate)
        hostname = (parsed.hostname or "").lower()
        if parsed.scheme not in {"http", "https"}:
            raise LinkedInJobImportError("A URL deve iniciar com http:// ou https://.")
        if hostname not in {"linkedin.com", "www.linkedin.com", "br.linkedin.com"} and not hostname.endswith(
            ".linkedin.com"
        ):
            raise LinkedInJobImportError("A URL informada não pertence ao LinkedIn.")
        if "/jobs/" not in parsed.path.lower():
            raise LinkedInJobImportError("A URL não parece apontar para uma vaga do LinkedIn.")
        return candidate

    @staticmethod
    def _build_prompt(url: str) -> str:
        return f"""
Pesquise na web os dados públicos da vaga indicada pela URL abaixo e devolva SOMENTE um objeto JSON válido, sem Markdown e sem comentários.

URL da vaga: {url}

Use exatamente estas chaves:
{{
  "title": "",
  "company_name": "",
  "location": "",
  "work_model": "Presencial|Híbrido|Remoto|",
  "employment_type": "CLT|PJ|Temporário|Estágio|Freelancer|Terceirizado|",
  "salary_min": null,
  "salary_max": null,
  "currency": "BRL|USD|EUR|GBP|",
  "recruiter": "",
  "published_at": "YYYY-MM-DD ou vazio",
  "application_deadline": "YYYY-MM-DD ou vazio",
  "description": "",
  "requirements": [],
  "responsibilities": [],
  "benefits": [],
  "linkedin_job_id": "",
  "confidence": "Alta|Média|Baixa",
  "source_references": []
}}

Regras:
- Não invente informações ausentes.
- Se o modelo de trabalho não puder ser determinado, use Presencial.
- Mantenha textos em português quando a vaga estiver em português.
- Converta salário somente quando o valor e a moeda estiverem explícitos.
- Em source_references, inclua URLs públicas efetivamente consultadas.
- Se o conteúdo do LinkedIn não estiver acessível, pesquise pelo ID, título e empresa visíveis na URL ou nos resultados públicos.
""".strip()

    @staticmethod
    def _extract_output_text(payload: dict[str, Any]) -> str:
        direct = payload.get("output_text")
        if isinstance(direct, str) and direct.strip():
            return direct.strip()

        parts: list[str] = []
        output = payload.get("output", [])
        if isinstance(output, list):
            for item in output:
                if not isinstance(item, dict) or item.get("type") != "message":
                    continue
                content = item.get("content", [])
                if not isinstance(content, list):
                    continue
                for content_item in content:
                    if not isinstance(content_item, dict):
                        continue
                    if content_item.get("type") == "output_text":
                        text = content_item.get("text")
                        if isinstance(text, str) and text.strip():
                            parts.append(text.strip())
        if not parts:
            raise LinkedInJobImportError(
                "A IA não retornou conteúdo suficiente para preencher a vaga."
            )
        return "\n".join(parts)

    @staticmethod
    def _parse_structured_json(text: str) -> dict[str, Any]:
        candidate = text.strip()
        if candidate.startswith("```"):
            candidate = re.sub(r"^```(?:json)?\s*", "", candidate, flags=re.IGNORECASE)
            candidate = re.sub(r"\s*```$", "", candidate)
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", candidate, flags=re.DOTALL)
            if match is None:
                raise LinkedInJobImportError(
                    "A resposta da importação não contém um JSON válido."
                ) from None
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError as exc:
                raise LinkedInJobImportError(
                    "A resposta da importação não contém um JSON válido."
                ) from exc
        if not isinstance(data, dict):
            raise LinkedInJobImportError("A resposta estruturada da vaga é inválida.")
        return data

    @classmethod
    def _to_result(cls, data: dict[str, Any], source_url: str) -> ImportedLinkedInJob:
        return ImportedLinkedInJob(
            title=cls._text(data.get("title")),
            company_name=cls._text(data.get("company_name")),
            location=cls._text(data.get("location")),
            work_model=cls._choice(data.get("work_model"), {"Presencial", "Híbrido", "Remoto"}) or "Presencial",
            employment_type=cls._choice(
                data.get("employment_type"),
                {"CLT", "PJ", "Temporário", "Estágio", "Freelancer", "Terceirizado"},
            ),
            salary_min=cls._number(data.get("salary_min")),
            salary_max=cls._number(data.get("salary_max")),
            currency=cls._choice(data.get("currency"), {"BRL", "USD", "EUR", "GBP"}) or "BRL",
            recruiter=cls._text(data.get("recruiter")),
            published_at=cls._date_text(data.get("published_at")),
            application_deadline=cls._date_text(data.get("application_deadline")),
            description=cls._text(data.get("description")),
            requirements=cls._string_tuple(data.get("requirements")),
            responsibilities=cls._string_tuple(data.get("responsibilities")),
            benefits=cls._string_tuple(data.get("benefits")),
            source_url=source_url,
            linkedin_job_id=cls._text(data.get("linkedin_job_id")) or cls._job_id_from_url(source_url),
            confidence=cls._choice(data.get("confidence"), {"Alta", "Média", "Baixa"}),
            source_references=cls._string_tuple(data.get("source_references")),
            accepting_applications=cls._optional_bool(
                data.get("accepting_applications")
            ),
        )

    @staticmethod
    def _optional_bool(value: Any) -> bool | None:
        if isinstance(value, bool):
            return value
        return None

    @staticmethod
    def _text(value: Any) -> str:
        return value.strip() if isinstance(value, str) else ""

    @staticmethod
    def _choice(value: Any, allowed: set[str]) -> str:
        text = value.strip() if isinstance(value, str) else ""
        return text if text in allowed else ""

    @staticmethod
    def _number(value: Any) -> float | None:
        if value in (None, ""):
            return None
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        return number if number >= 0 else None

    @staticmethod
    def _date_text(value: Any) -> str:
        text = value.strip() if isinstance(value, str) else ""
        return text if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text) else ""

    @staticmethod
    def _string_tuple(value: Any) -> tuple[str, ...]:
        if not isinstance(value, list):
            return ()
        return tuple(item.strip() for item in value if isinstance(item, str) and item.strip())

    @staticmethod
    def _job_id_from_url(url: str) -> str:
        match = re.search(r"(?:currentJobId=|/view/(?:[^/?]+-)?)(\d{6,})", url)
        return match.group(1) if match else ""

    @staticmethod
    def _parse_timeout(value: str) -> float:
        try:
            timeout = float(value)
        except ValueError:
            return 120.0
        return max(15.0, min(timeout, 300.0))

    @staticmethod
    def _http_error_message(status: int, details: str) -> str:
        if status == 401:
            return "A chave da OpenAI foi recusada. Verifique e teste a chave na página Configurações."
        if status == 403:
            return "A chave não possui permissão para realizar esta importação."
        if status == 429:
            return "A OpenAI limitou a solicitação ou o saldo disponível foi atingido."
        if status >= 500:
            return "A OpenAI está temporariamente indisponível. Tente novamente."
        try:
            payload = json.loads(details)
            message = payload.get("error", {}).get("message", "")
        except json.JSONDecodeError:
            message = ""
        return message or f"A OpenAI recusou a importação (HTTP {status})."
