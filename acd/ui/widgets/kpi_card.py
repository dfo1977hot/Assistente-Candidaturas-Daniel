from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class KPICard(QFrame):
    def __init__(self, titulo: str, valor: str) -> None:
        super().__init__()

        self.setStyleSheet(
            """
            QFrame{
                background:white;
                border:1px solid #d1d5db;
                border-radius:10px;
                padding:10px;
            }
            """
        )

        layout = QVBoxLayout()

        self.titulo_label = QLabel(titulo)
        self.titulo_label.setStyleSheet("font-size:12px;color:#6b7280;")

        self.valor_label = QLabel(valor)
        self.valor_label.setStyleSheet(
            """
            font-size:24px;
            font-weight:bold;
            """
        )

        layout.addWidget(self.titulo_label)
        layout.addWidget(self.valor_label)

        self.setLayout(layout)

    def set_value(self, valor: str) -> None:
        self.valor_label.setText(valor)