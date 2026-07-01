from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QLabel


class BasePage(QWidget):

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