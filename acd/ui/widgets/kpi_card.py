from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class KPICard(QFrame):

    def __init__(self, titulo, valor):

        super().__init__()

        self.setStyleSheet("""
            QFrame{
                background:white;
                border:1px solid #d1d5db;
                border-radius:10px;
                padding:10px;
            }
        """)

        layout = QVBoxLayout()

        titulo_label = QLabel(titulo)
        titulo_label.setStyleSheet("font-size:12px;color:#6b7280;")

        valor_label = QLabel(valor)
        valor_label.setStyleSheet("""
            font-size:24px;
            font-weight:bold;
        """)

        layout.addWidget(titulo_label)
        layout.addWidget(valor_label)

        self.setLayout(layout)