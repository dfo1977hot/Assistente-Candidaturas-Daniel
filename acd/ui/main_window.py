from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QStatusBar,
    QStackedWidget,
)

from acd.core.router import Router
from acd.presentation.pages.application_page import ApplicationPage
from acd.presentation.pages.company_page import CompanyPage
from acd.presentation.pages.curriculum_page import CurriculumPage
from acd.presentation.pages.interview_page import InterviewPage
from acd.presentation.pages.job_page import JobPage
from acd.presentation.pages.workflow_page import WorkflowPage
from acd.presentation.pages.analytics_page import AnalyticsPage
from acd.presentation.pages.career_page import CareerPage
from acd.presentation.pages.assistant_page import AssistantPage
from acd.presentation.pages.agent_console_page import AgentConsolePage
from acd.presentation.pages.ai_resume_page import AIResumePage
from acd.presentation.pages.ats_page import ATSPage
from acd.presentation.pages.base_page import BasePage
from acd.ui.sidebar import Sidebar
from acd.ui.dashboard import Dashboard


class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("Assistente de Candidaturas do Daniel")

        self.resize(1400, 800)

        central = QWidget()

        layout = QHBoxLayout()

        self.sidebar = Sidebar()

        # Área principal
        self.stack = QStackedWidget()

        # Dashboard
        self.dashboard = Dashboard()
        self.company_page = CompanyPage()
        self.job_page = JobPage()
        self.application_page = ApplicationPage()
        self.interview_page = InterviewPage()
        self.curriculum_page = CurriculumPage()
        self.workflow_page = WorkflowPage()
        self.analytics_page = AnalyticsPage()
        self.career_page = CareerPage()
        self.assistant_page = AssistantPage()
        self.agent_console_page = AgentConsolePage()
        self.cover_letters_page = AIResumePage()
        self.crm_page = ATSPage()
        self.settings_page = BasePage("Configuracoes")

        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.company_page)
        self.stack.addWidget(self.job_page)
        self.stack.addWidget(self.application_page)
        self.stack.addWidget(self.interview_page)
        self.stack.addWidget(self.curriculum_page)
        self.stack.addWidget(self.workflow_page)
        self.stack.addWidget(self.analytics_page)
        self.stack.addWidget(self.career_page)
        self.stack.addWidget(self.assistant_page)
        self.stack.addWidget(self.agent_console_page)
        self.stack.addWidget(self.cover_letters_page)
        self.stack.addWidget(self.crm_page)
        self.stack.addWidget(self.settings_page)

        self.router = Router()
        self.router.set_stack(self.stack)
        self.router.register("dashboard", self.dashboard)
        self.router.register("companies", self.company_page)
        self.router.register("jobs", self.job_page)
        self.router.register("applications", self.application_page)
        self.router.register("interviews", self.interview_page)
        self.router.register("curricula", self.curriculum_page)
        self.router.register("workflows", self.workflow_page)
        self.router.register("analytics", self.analytics_page)
        self.router.register("career", self.career_page)
        self.router.register("assistant", self.assistant_page)
        self.router.register("agent_console", self.agent_console_page)
        self.router.register("cover_letters", self.cover_letters_page)
        self.router.register("crm", self.crm_page)
        self.router.register("settings", self.settings_page)

        self.sidebar.itemClicked.connect(self._on_sidebar_item_clicked)

        layout.addWidget(self.sidebar)

        layout.addWidget(self.stack)

        central.setLayout(layout)

        self.setCentralWidget(central)

        status = QStatusBar()

        status.showMessage("ACD v0.1.0")

        self.setStatusBar(status)

    def _on_sidebar_item_clicked(self, item):
        label = item.text()
        if "Empresas" in label:
            self.router.navigate("companies")
        elif "Vagas" in label:
            self.router.navigate("jobs")
        elif "Candidaturas" in label:
            self.router.navigate("applications")
        elif "Entrevistas" in label:
            self.router.navigate("interviews")
        elif "Currículos" in label:
            self.router.navigate("curricula")
        elif "Workflow" in label:
            self.router.navigate("workflows")
        elif "Análise" in label or "Analytics" in label:
            self.router.navigate("analytics")
        elif "Planejamento" in label or "Carreira" in label:
            self.router.navigate("career")
        elif "Assistente" in label or "IA" in label:
            self.router.navigate("assistant")
        elif "Agentes" in label:
            self.router.navigate("agent_console")
        elif "Cartas" in label:
            self.router.navigate("cover_letters")
        elif "CRM" in label:
            self.router.navigate("crm")
        elif "Config" in label:
            self.router.navigate("settings")
        elif "Dashboard" in label:
            self.router.navigate("dashboard")
