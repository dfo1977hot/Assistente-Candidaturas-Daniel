"""Research a public professional recruiter/RH e-mail when the vacancy omits it."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re

from acd.infrastructure.ai.providers import AIProvider, SettingsConfiguredAIProvider
from acd.services.settings_service import SettingsService


@dataclass(frozen=True, slots=True)
class RecruiterEmailResearchRequest:
    company_name: str
    job_title: str
    location: str = ""
    recruiter_name: str = ""


class RecruiterEmailResearchService:
    """Find only publicly disclosed professional contact e-mails."""

    def __init__(
        self,
        settings_service: SettingsService | None = None,
        ai_provider: AIProvider | None = None,
    ) -> None:
        self._settings_service = settings_service or SettingsService()
        self._ai_provider = ai_provider or SettingsConfiguredAIProvider(
            self._settings_service
        )

    def research(self, request: RecruiterEmailResearchRequest) -> str:
        if not request.company_name.strip():
            return ""

        prompt = (
            "Pesquise na web um e-mail PROFISSIONAL e PUBLICAMENTE DIVULGADO de "
            "recrutamento/RH relacionado à empresa e, quando possível, à vaga abaixo. "
            "Não deduza, não gere e não adivinhe padrões de e-mail. "
            "Aceite somente um endereço explicitamente publicado em uma fonte pública. "
            "Se não houver evidência suficiente, retorne email vazio. "
            "Responda somente JSON no formato {\"email\": \"...\"}.\n\n"
            f"Empresa: {request.company_name}\n"
            f"Vaga: {request.job_title}\n"
            f"Local: {request.location}\n"
            f"Recrutador informado: {request.recruiter_name}"
        )

        try:
            raw = self._ai_provider.generate_text(
                prompt=prompt,
                model="recruiter-email-research",
                temperature=0.0,
                max_tokens=500,
                language="pt-BR",
            ).strip()
        except Exception:
            return ""

        email = self._extract_email_from_response(raw)
        return email

    @staticmethod
    def _extract_email_from_response(raw: str) -> str:
        text = raw.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\s*```$", "", text)

        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = {}

        candidate = str(payload.get("email", "")).strip() if isinstance(payload, dict) else ""
        if not candidate:
            match = re.search(
                r"(?<![\w.+-])([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})(?![\w.-])",
                raw,
                flags=re.IGNORECASE,
            )
            candidate = match.group(1) if match else ""

        if not candidate:
            return ""

        blocked = ("example.com", "noreply", "no-reply", "donotreply", "do-not-reply")
        normalized = candidate.casefold()
        return "" if any(value in normalized for value in blocked) else candidate
