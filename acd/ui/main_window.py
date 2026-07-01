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

        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.company_page)
        self.stack.addWidget(self.job_page)
        self.stack.addWidget(self.application_page)
        self.stack.addWidget(self.interview_page)
        self.stack.addWidget(self.curriculum_page)

        self.router = Router()
        self.router.set_stack(self.stack)
        self.router.register("dashboard", self.dashboard)
        self.router.register("companies", self.company_page)
        self.router.register("jobs", self.job_page)
        self.router.register("applications", self.application_page)
        self.router.register("interviews", self.interview_page)
        self.router.register("curricula", self.curriculum_page)

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
        elif "Dashboard" in label:
            self.router.navigate("dashboard")
