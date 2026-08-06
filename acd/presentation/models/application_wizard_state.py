from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ApplicationWizardState:
    """
    Estado temporário do fluxo de Nova Candidatura.

    Este objeto pertence exclusivamente à camada de apresentação e
    armazena todas as informações preenchidas pelo usuário durante
    o Wizard.

    Ao final do fluxo, esses dados serão enviados à ApplicationFacade,
    que executará os casos de uso necessários.
    """

    company_name: str = ""
    job_title: str = ""
    job_url: str = ""
    job_description: str = ""

    analysis_result: object | None = None

    selected_resume: str | None = None

    generated_resume: str | None = None

    generated_cover_letter: str | None = None

    metadata: dict[str, object] = field(default_factory=dict)

    def clear(self) -> None:
        self.company_name = ""
        self.job_title = ""
        self.job_url = ""
        self.job_description = ""

        self.analysis_result = None

        self.selected_resume = None

        self.generated_resume = None

        self.generated_cover_letter = None

        self.metadata.clear()