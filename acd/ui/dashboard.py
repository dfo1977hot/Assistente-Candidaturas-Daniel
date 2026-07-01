from PySide6.QtWidgets import QGridLayout

from acd.presentation.pages.base_page import BasePage
from acd.services.application_service import ApplicationService
from acd.services.company_service import CompanyService
from acd.services.interview_service import InterviewService
from acd.services.job_service import JobService
from acd.ui.widgets.kpi_card import KPICard


class Dashboard(BasePage):

    def __init__(self):

        super().__init__("Dashboard")

        self.company_service = CompanyService()
        self.job_service = JobService()
        self.application_service = ApplicationService()
        self.interview_service = InterviewService()
        principal = self.layout

        grid = QGridLayout()

        self.total_companies_card = KPICard("Total Empresas", "0")
        self.total_jobs_card = KPICard("Total Vagas", "0")
        self.total_applications_card = KPICard("Total Candidaturas", "0")
        self.total_interviews_card = KPICard("Total Entrevistas", "0")
        self.today_interviews_card = KPICard("Entrevistas Hoje", "0")
        grid.addWidget(self.total_interviews_card, 0, 0)
        grid.addWidget(self.today_interviews_card, 0, 1)
        grid.addWidget(self.total_companies_card, 0, 2)
        grid.addWidget(self.total_jobs_card, 0, 3)
        grid.addWidget(self.total_applications_card, 0, 4)

        principal.addLayout(grid)
        self.refresh_kpis()

    def refresh_kpis(self) -> None:
        self.total_companies_card.set_value(str(self.company_service.count_companies()))
        self.total_jobs_card.set_value(str(self.job_service.count_jobs()))
        self.total_applications_card.set_value(str(self.application_service.get_statistics().get("total", 0)))
        statistics = self.interview_service.get_statistics()
        self.total_interviews_card.set_value(str(statistics.get("total", 0)))
        self.today_interviews_card.set_value(str(statistics.get("today", 0)))