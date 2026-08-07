from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class BasePage(QWidget):
    """
    Classe base para todas as páginas da camada de apresentação.

    Além do layout comum, fornece pontos de extensão para fluxos
    baseados em Wizard.
    """

    def __init__(self, titulo: str):
        super().__init__()

        self.layout = QVBoxLayout()

        self.title = QLabel(titulo)

        self.title.setStyleSheet("""
            font-size:28px;
            font-weight:bold;
            margin-bottom:20px;
        """)

        self.layout.addWidget(self.title)

        self.setLayout(self.layout)

    def on_enter(self) -> None:
        """
        Executado quando a página se torna ativa.
        """

    def on_leave(self) -> None:
        """
        Executado antes da página ser substituída.
        """

    def validate_page(self) -> bool:
        """
        Permite que páginas do Wizard validem seus dados antes
        da navegação.
        """
        return True