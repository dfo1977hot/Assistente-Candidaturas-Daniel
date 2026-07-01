from PySide6.QtWidgets import QGridLayout

from acd.presentation.pages.base_page import BasePage
from acd.services.company_service import CompanyService
from acd.services.job_service import JobService
from acd.ui.widgets.kpi_card import KPICard


class Dashboard(BasePage):

    def __init__(self):

        super().__init__("Dashboard")

        self.company_service = CompanyService()
        self.job_service = JobService()
        principal = self.layout

        grid = QGridLayout()

        self.total_companies_card = KPICard("Total Empresas", "0")
        self.total_jobs_card = KPICard("Total Vagas", "0")
        grid.addWidget(KPICard("Candidaturas", "0"), 0, 0)
        grid.addWidget(KPICard("Entrevistas", "0"), 0, 1)
        grid.addWidget(KPICard("Aderência Média", "0%"), 0, 2)
        grid.addWidget(self.total_companies_card, 0, 3)
        grid.addWidget(self.total_jobs_card, 0, 4)

        principal.addLayout(grid)
        self.refresh_kpis()

    def refresh_kpis(self) -> None:
        self.total_companies_card.set_value(str(self.company_service.count_companies()))
        self.total_jobs_card.set_value(str(self.job_service.count_jobs()))