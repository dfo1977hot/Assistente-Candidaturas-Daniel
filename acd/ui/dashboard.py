from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QSizePolicy, QWidget

from acd.presentation.pages.base_page import BasePage
from acd.services.application_service import ApplicationService
from acd.services.company_service import CompanyService
from acd.services.curriculum_service import CurriculumService
from acd.services.interview_service import InterviewService
from acd.services.job_service import JobService
from acd.ui.widgets.kpi_card import KPICard


class Dashboard(BasePage):
    HISTORY_DAYS = 14

    def __init__(
        self,
        company_service: CompanyService,
        job_service: JobService,
        application_service: ApplicationService,
        interview_service: InterviewService,
        curriculum_service: CurriculumService,
    ) -> None:
        super().__init__("Dashboard")

        self.company_service = company_service
        self.job_service = job_service
        self.application_service = application_service
        self.interview_service = interview_service
        self.curriculum_service = curriculum_service

        self.total_companies_card = KPICard("Total Empresas", "0")
        self.total_jobs_card = KPICard("Total Vagas", "0")
        self.total_applications_card = KPICard("Total Candidaturas", "0")
        self.total_interviews_card = KPICard("Total Entrevistas", "0")
        self.today_interviews_card = KPICard("Entrevistas Hoje", "0")
        self.total_curricula_card = KPICard("Total Currículos", "0")
        self.most_used_curriculum_card = KPICard("Currículo mais usado", "0")

        cards = (
            self.total_interviews_card,
            self.today_interviews_card,
            self.total_companies_card,
            self.total_jobs_card,
            self.total_applications_card,
            self.total_curricula_card,
            self.most_used_curriculum_card,
        )

        cards_container = QWidget()
        cards_layout = QGridLayout(cards_container)
        cards_layout.setContentsMargins(8, 8, 8, 8)
        cards_layout.setHorizontalSpacing(14)
        cards_layout.setVerticalSpacing(14)

        columns = 4
        for index, card in enumerate(cards):
            row, column = divmod(index, columns)
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            cards_layout.addWidget(card, row, column)

        for column in range(columns):
            cards_layout.setColumnStretch(column, 1)

        self.layout.addWidget(cards_container)
        self.layout.addStretch(1)
        self.refresh_kpis()

    def refresh_reference_data(self) -> None:
        self.refresh_kpis()

    def refresh_kpis(self) -> None:

        application_stats = self.application_service.get_statistics()
        interview_stats = self.interview_service.get_statistics()
        curriculum_stats = self.curriculum_service.get_statistics()

        self.total_companies_card.set_value(str(self.company_service.count_companies()))
        self.total_jobs_card.set_value(str(self.job_service.count_jobs()))
        self.total_applications_card.set_value(str(application_stats.get("total", 0)))
        self.total_interviews_card.set_value(str(interview_stats.get("total", 0)))
        self.today_interviews_card.set_value(str(interview_stats.get("today", 0)))
        self.total_curricula_card.set_value(str(curriculum_stats.get("total", 0)))
        self.most_used_curriculum_card.set_value(str(curriculum_stats.get("used", 0)))
