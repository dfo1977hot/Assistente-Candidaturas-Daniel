from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ApplicationDraft:
    """
    Representa o rascunho de uma candidatura durante o fluxo do Wizard.

    Este objeto é mutável e existe apenas enquanto o usuário preenche
    as informações necessárias para iniciar uma candidatura.
    """

    company_name: str = ""
    job_title: str = ""
    job_description: str = ""

    def clear(self) -> None:
        """Limpa todas as informações do rascunho."""
        self.company_name = ""
        self.job_title = ""
        self.job_description = ""