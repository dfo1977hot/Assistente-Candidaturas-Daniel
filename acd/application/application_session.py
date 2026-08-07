from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ApplicationSession:
    """
    Estado temporário do fluxo de uma candidatura.

    A sessão existe apenas enquanto o usuário está preparando uma
    candidatura. Ela ainda não representa um registro persistido
    no banco de dados.
    """

    company_name: str = ""
    job_title: str = ""
    job_url: str = ""
    job_description: str = ""

    company_id: int | None = None
    job_id: int | None = None
    application_id: int | None = None

    analysis_result: Any | None = None

    selected_resume: str | None = None
    generated_resume: str | None = None
    generated_cover_letter: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def has_job_description(self) -> bool:
        return bool(self.job_description.strip())

    @property
    def is_analyzed(self) -> bool:
        return self.analysis_result is not None

    @property
    def has_resume(self) -> bool:
        return self.generated_resume is not None

    @property
    def is_registered(self) -> bool:
        return self.application_id is not None

    def clear_analysis(self) -> None:
        """Remove os resultados da análise atual."""
        self.analysis_result = None

    def reset(self) -> None:
        """Reinicia completamente a sessão."""
        self.company_name = ""
        self.job_title = ""
        self.job_url = ""
        self.job_description = ""

        self.company_id = None
        self.job_id = None
        self.application_id = None

        self.analysis_result = None

        self.selected_resume = None
        self.generated_resume = None
        self.generated_cover_letter = None

        self.metadata.clear()