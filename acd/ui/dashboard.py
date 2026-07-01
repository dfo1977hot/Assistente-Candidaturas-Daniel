from PySide6.QtWidgets import QGridLayout

from acd.presentation.pages.base_page import BasePage
from acd.ui.widgets.kpi_card import KPICard


class Dashboard(BasePage):

    def __init__(self):

        super().__init__("Dashboard")

        principal = self.layout

        grid = QGridLayout()

        grid.addWidget(KPICard("Candidaturas", "0"), 0, 0)
        grid.addWidget(KPICard("Entrevistas", "0"), 0, 1)
        grid.addWidget(KPICard("Aderência Média", "0%"), 0, 2)
        grid.addWidget(KPICard("Follow-ups", "0"), 0, 3)

        principal.addLayout(grid)