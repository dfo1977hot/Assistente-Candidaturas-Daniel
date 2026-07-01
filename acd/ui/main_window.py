from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QStatusBar,
    QStackedWidget,
)

from acd.core.router import Router
from acd.presentation.pages.company_page import CompanyPage
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

        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.company_page)

        self.router = Router()
        self.router.set_stack(self.stack)
        self.router.register("dashboard", self.dashboard)
        self.router.register("companies", self.company_page)

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
        elif "Dashboard" in label:
            self.router.navigate("dashboard")
