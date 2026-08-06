from __future__ import annotations

from abc import ABC, abstractmethod

from PySide6.QtWidgets import QWidget

from acd.presentation.models.application_wizard_state import (
    ApplicationWizardState,
)


class WizardPage(QWidget, ABC):
    """
    Classe base para todas as páginas do Wizard.

    Cada página conhece apenas o estado compartilhado do Wizard.
    Não conhece ApplicationFacade, ApplicationSession ou banco de dados.
    """

    def __init__(
        self,
        state: ApplicationWizardState,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._state = state

    @property
    def state(self) -> ApplicationWizardState:
        """
        Retorna o estado compartilhado do Wizard.
        """
        return self._state

    @abstractmethod
    def validate_page(self) -> bool:
        """
        Valida os dados da página antes do avanço.
        """

    @abstractmethod
    def save_state(self) -> None:
        """
        Persiste os dados da interface no estado compartilhado.
        """

    @abstractmethod
    def load_state(self) -> None:
        """
        Carrega os dados do estado compartilhado para a interface.
        """

    def on_enter(self) -> None:
        """
        Executado quando a página passa a ser exibida.

        Implementação padrão:
            - recarrega os dados do estado.
        """
        self.load_state()

    def on_leave(self) -> None:
        """
        Executado antes da navegação para outra página.

        Implementação padrão:
            - salva os dados no estado.
        """
        self.save_state()