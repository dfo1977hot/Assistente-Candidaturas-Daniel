from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout


class KPICard(QFrame):
    """Card compacto para exibição de um indicador do Dashboard."""

    def __init__(self, title: str, value: str = "0") -> None:
        super().__init__()
        self.setObjectName("kpiCard")
        self.setMinimumSize(190, 120)
        self.setMaximumHeight(145)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setWordWrap(True)

        self.value_label = QLabel(value)
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setObjectName("kpiValue")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)
        layout.addWidget(self.title_label)
        layout.addStretch(1)
        layout.addWidget(self.value_label)
        layout.addStretch(1)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)

    def set_history(self, values: Sequence[int | float]) -> None:
        """Mantém compatibilidade com chamadas antigas, sem renderizar gráfico."""
        del values
