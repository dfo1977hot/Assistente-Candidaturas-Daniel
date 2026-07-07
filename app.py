import sys

from PySide6.QtWidgets import QApplication

from acd.core.theme_manager import ThemeManager
from acd.database.create_database import create_database
from acd.ui.main_window import MainWindow


def main():

    # Cria o banco de dados (caso ainda não exista)
    create_database()

    # Inicializa a aplicação Qt
    app = QApplication(sys.argv)

    # Aplica o tema da aplicação
    ThemeManager.load(app)

    # Cria a janela principal
    janela = MainWindow()

    # Exibe a janela
    janela.show()

    # Inicia o loop da aplicação
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
