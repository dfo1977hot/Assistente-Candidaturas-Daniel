from __future__ import annotations

from acd.core.logger import logger
from acd.domain.entities.job_profile import JobProfile
from acd.infrastructure.parsers.text_parser import TextParser
from acd.infrastructure.repositories.job_profile_repository import JobProfileRepository


class JobAnalysisService:
    """Serviço para parser e estruturação de descrições de vagas."""

    def __init__(self, repository: JobProfileRepository | None = None) -> None:
        self.repository = repository or JobProfileRepository()
        self.parser = TextParser()

    def analyze_job(self, *, job_id: int, raw_description: str) -> JobProfile | None:
        """Analisa uma descrição de vaga e persiste o perfil estruturado."""
        parsed = self.parser.parse(raw_description)
        profile = JobProfile(
            job_id=job_id,
            raw_description=raw_description.strip(),
            structured_description=self._build_structured_description(parsed),
            seniority=self._select_seniority(parsed.get("seniority", [])),
            work_model="",
            language="",
            experience_years=None,
            skills=",".join(parsed.get("skills", [])),
            technologies=",".join(parsed.get("technologies", [])),
            methodologies=",".join(parsed.get("methodologies", [])),
            languages=",".join(parsed.get("languages", [])),
            certifications=",".join(parsed.get("certifications", [])),
            keywords=",".join(
                parsed.get("skills", [])
                + parsed.get("technologies", [])
                + parsed.get("methodologies", [])
            ),
        )
        created = self.repository.create(profile)
        logger.info("Vaga analisada: %s", created.id)
        return created

    def get_statistics(self) -> dict[str, object]:
        """Retorna estatísticas básicas para o dashboard."""
        return self.repository.get_statistics()

    def _build_structured_description(self, parsed: dict[str, list[str]]) -> str:
        return "; ".join(
            [
                f"Competências: {', '.join(parsed.get('skills', [])) or 'Nenhuma'}",
                f"Tecnologias: {', '.join(parsed.get('technologies', [])) or 'Nenhuma'}",
                f"Metodologias: {', '.join(parsed.get('methodologies', [])) or 'Nenhuma'}",
                f"Idiomas: {', '.join(parsed.get('languages', [])) or 'Nenhum'}",
                f"Certificações: {', '.join(parsed.get('certifications', [])) or 'Nenhuma'}",
            ]
        )

    def _select_seniority(self, seniority: list[str]) -> str:
        if not seniority:
            return "Não informada"
        return seniority[0]
