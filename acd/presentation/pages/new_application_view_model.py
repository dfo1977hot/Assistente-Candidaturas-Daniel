from __future__ import annotations

from acd.application.application_facade import ApplicationFacade
from acd.application.application_snapshot import ApplicationSnapshot
from acd.presentation.models.application_wizard_state import (
    ApplicationWizardState,
)


class NewApplicationViewModel:
    """
    ViewModel responsável pelo fluxo de Nova Candidatura.

    É o único proprietário do estado temporário do Wizard e faz a
    ponte entre a interface e a camada de aplicação.
    """

    def __init__(
        self,
        facade: ApplicationFacade | None = None,
    ) -> None:
        self._facade = facade or ApplicationFacade()
        self._state = ApplicationWizardState()

    @property
    def state(self) -> ApplicationWizardState:
        """
        Estado compartilhado entre as páginas do Wizard.
        """
        return self._state

    @property
    def snapshot(self) -> ApplicationSnapshot:
        """
        Retorna o snapshot atual da candidatura.
        """
        return self._facade.snapshot()

    @property
    def company_name(self) -> str:
        return self._state.company_name

    @property
    def job_title(self) -> str:
        return self._state.job_title

    @property
    def job_url(self) -> str:
        return self._state.job_url

    @property
    def job_description(self) -> str:
        return self._state.job_description

    # ==========================================================
    # API do Wizard
    # ==========================================================

    def start_application(
        self,
        company_name: str | None = None,
        job_title: str | None = None,
        job_description: str | None = None,
    ) -> ApplicationSnapshot:
        """
        Inicia uma candidatura.

        Se os parâmetros forem informados, o estado do Wizard é
        atualizado antes da chamada à camada de aplicação.

        Isso mantém compatibilidade com a API anterior e também
        permite que o Wizard utilize apenas o estado compartilhado.
        """

        if company_name is not None:
            self.set_company_name(company_name)

        if job_title is not None:
            self.set_job_title(job_title)

        if job_description is not None:
            self.set_job_description(job_description)

        self._facade.start_application(
            company_name=self._state.company_name,
            job_title=self._state.job_title,
            job_description=self._state.job_description,
        )

        return self.snapshot

    def clear(self) -> ApplicationSnapshot:
        """
        Limpa o estado do Wizard e a sessão da aplicação.

        Retorna o snapshot atualizado.
        """

        self._state.clear()
        self._facade.clear()

        return self.snapshot

    def reset(self) -> None:
        """
        Limpa o estado do Wizard e a sessão da aplicação.
        """
        self._state.clear()
        self._facade.clear()

    # ==========================================================
    # Métodos auxiliares para manipulação do estado
    # ==========================================================

    def set_company_name(self, value: str) -> None:
        self._state.company_name = value.strip()

    def set_job_title(self, value: str) -> None:
        self._state.job_title = value.strip()

    def set_job_url(self, value: str) -> None:
        self._state.job_url = value.strip()

    def set_job_description(self, value: str) -> None:
        self._state.job_description = value.strip()