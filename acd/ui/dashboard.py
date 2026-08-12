from __future__ import annotations

from typing import Any, Protocol

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from acd.presentation.long_running_task_executor import LongRunningTaskExecutor
from acd.presentation.pages.base_page import BasePage
from acd.services.analytics_service import AnalyticsFilters, DashboardSnapshot
from acd.ui.widgets.kpi_card import KPICard


class AnalyticsGateway(Protocol):
    PERIODS: tuple[str, ...]

    def get_dashboard(self, filters: AnalyticsFilters | None = None) -> DashboardSnapshot: ...


class EventGateway(Protocol):
    def subscribe(self, event_type: str, handler: Any) -> None: ...


class Dashboard(BasePage):
    """Operational dashboard rendering only AnalyticsService DTOs."""

    refresh_requested = Signal()
    RELEVANT_EVENTS = (
        "job.created",
        "job.imported",
        "application.created",
        "application.status_changed",
        "workflow.execution_changed",
    )

    def __init__(
        self,
        analytics_service: AnalyticsGateway,
        event_bus: EventGateway | None = None,
    ) -> None:
        super().__init__("Dashboard")
        self.analytics_service = analytics_service
        self._executor = LongRunningTaskExecutor(self)
        self._loaded_once = False
        self._options_loaded = False
        self._build_filters()
        self._build_kpis()
        self._build_views()
        self._executor.started.connect(self._on_loading)
        self._executor.succeeded.connect(self._apply_snapshot)
        self._executor.failed.connect(self._on_error)
        self._executor.finished.connect(self._on_finished)
        self.refresh_requested.connect(self.refresh_kpis)
        if event_bus is not None:
            for event_type in self.RELEVANT_EVENTS:
                event_bus.subscribe(event_type, self._on_domain_event)

    def _build_filters(self) -> None:
        row = QHBoxLayout()
        self.period_combo = QComboBox()
        self.period_combo.addItems(self.analytics_service.PERIODS)
        self.period_combo.setCurrentText("30 dias")
        self.start_date = QDateEdit(QDate.currentDate().addDays(-29))
        self.end_date = QDateEdit(QDate.currentDate())
        for editor in (self.start_date, self.end_date):
            editor.setCalendarPopup(True)
            editor.setDisplayFormat("dd/MM/yyyy")
            editor.setEnabled(False)
        self.company_combo = QComboBox()
        self.company_combo.addItem("Todas as empresas", None)
        self.text_filter = QLineEdit()
        self.text_filter.setPlaceholderText("Cargo ou texto")
        self.status_combo = QComboBox()
        self.status_combo.addItem("Todos os status", "")
        self.source_combo = QComboBox()
        self.source_combo.addItem("Todas as origens", "")
        self.refresh_button = QPushButton("Atualizar")
        self.refresh_button.clicked.connect(self.refresh_kpis)
        self.period_combo.currentTextChanged.connect(self._toggle_custom_dates)
        for label, widget in (
            ("Período", self.period_combo),
            ("De", self.start_date),
            ("Até", self.end_date),
            ("Empresa", self.company_combo),
            ("Cargo", self.text_filter),
            ("Status", self.status_combo),
            ("Origem", self.source_combo),
        ):
            row.addWidget(QLabel(label))
            row.addWidget(widget)
        row.addWidget(self.refresh_button)
        self.layout.addLayout(row)
        self.query_status = QLabel("Clique em Atualizar para consultar os dados reais do ACD.")
        self.layout.addWidget(self.query_status)

    def _build_kpis(self) -> None:
        specs = (
            ("jobs_total", "Vagas cadastradas"),
            ("jobs_active", "Vagas abertas/ativas"),
            ("applications_total", "Candidaturas totais"),
            ("applications_in_progress", "Candidaturas em andamento"),
            ("interviews", "Entrevistas"),
            ("offers", "Ofertas"),
            ("closed_or_rejected", "Rejeições/encerradas"),
            ("application_to_interview_rate", "Candidatura → entrevista"),
            ("interview_to_offer_rate", "Entrevista → oferta"),
            ("active_workflows", "Workflows ativos"),
            ("workflows_running", "Workflows em andamento"),
            ("workflows_awaiting_user", "Aguardando usuário"),
            ("recent_failures", "Falhas recentes"),
            ("next_scheduled_run", "Próxima execução"),
            ("cover_letters", "Cartas geradas"),
            ("optimized_resumes", "Currículos otimizados"),
        )
        self.kpi_cards = {key: KPICard(title, "0") for key, title in specs}
        container = QWidget()
        grid = QGridLayout(container)
        for index, card in enumerate(self.kpi_cards.values()):
            grid.addWidget(card, index // 4, index % 4)
        self.layout.addWidget(container)
        # Compatibility aliases used by the established dashboard checks.
        self.total_companies_card = KPICard("Empresas no filtro", "0")
        self.total_jobs_card = self.kpi_cards["jobs_total"]
        self.total_applications_card = self.kpi_cards["applications_total"]
        self.total_interviews_card = self.kpi_cards["interviews"]
        self.today_interviews_card = self.kpi_cards["workflows_running"]
        self.total_curricula_card = self.kpi_cards["optimized_resumes"]
        self.most_used_curriculum_card = self.kpi_cards["cover_letters"]

    def _build_views(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.addWidget(QLabel("Funil por status real"))
        self.funnel_container = QWidget()
        self.funnel_layout = QVBoxLayout(self.funnel_container)
        body_layout.addWidget(self.funnel_container)
        body_layout.addWidget(QLabel("Tendência temporal"))
        self.trend_table = QTableWidget(0, 5)
        self.trend_table.setHorizontalHeaderLabels(
            ["Período", "Vagas", "Candidaturas", "Entrevistas", "Ofertas"]
        )
        body_layout.addWidget(self.trend_table)
        body_layout.addWidget(QLabel("Últimas execuções de workflows"))
        self.workflow_table = QTableWidget(0, 4)
        self.workflow_table.setHorizontalHeaderLabels(
            ["ID", "Workflow", "Status", "Início"]
        )
        body_layout.addWidget(self.workflow_table)
        body_layout.addWidget(QLabel("Alertas operacionais"))
        self.alerts_list = QListWidget()
        body_layout.addWidget(self.alerts_list)
        scroll.setWidget(body)
        self.layout.addWidget(scroll)

    def refresh_reference_data(self) -> None:
        self.refresh_kpis()

    def closeEvent(self, event: object) -> None:
        self.shutdown()
        super().closeEvent(event)

    def shutdown(self) -> None:
        """Finish the owned worker safely before the parent window is destroyed."""
        if self._executor.is_running:
            self._executor.cancel()
            self._executor.wait_for_finished()

    def refresh_kpis(self) -> None:
        if self._executor.is_running:
            return
        filters = self._selected_filters()
        self._executor.execute(lambda: self.analytics_service.get_dashboard(filters))

    def _selected_filters(self) -> AnalyticsFilters:
        custom = self.period_combo.currentText() == "Personalizado"
        return AnalyticsFilters(
            period=self.period_combo.currentText(),
            start_date=self.start_date.date().toPython() if custom else None,
            end_date=self.end_date.date().toPython() if custom else None,
            company_id=self.company_combo.currentData(),
            text=self.text_filter.text(),
            application_status=str(self.status_combo.currentData() or ""),
            source=str(self.source_combo.currentData() or ""),
        )

    def _toggle_custom_dates(self, period: str) -> None:
        enabled = period == "Personalizado"
        self.start_date.setEnabled(enabled)
        self.end_date.setEnabled(enabled)

    def _on_loading(self) -> None:
        self.refresh_button.setEnabled(False)
        self.query_status.setText("Atualizando dados…")

    def _on_finished(self) -> None:
        self.refresh_button.setEnabled(True)

    def _on_error(self, error: object) -> None:
        self.query_status.setText("Não foi possível consultar o Dashboard.")
        QMessageBox.warning(self, "Dashboard", f"Erro ao consultar dados: {error}")

    def _apply_snapshot(self, snapshot: DashboardSnapshot) -> None:
        self._loaded_once = True
        for key, card in self.kpi_cards.items():
            value = snapshot.kpis.get(key)
            if key.endswith("_rate"):
                card.set_value(f"{float(value or 0):.1f}%")
            else:
                card.set_value("—" if value is None else str(value))
        self.total_companies_card.set_value(str(len(snapshot.options["companies"])))
        self.query_status.setText(
            snapshot.period_label if snapshot.has_data else "Sem dados no período"
        )
        self._render_funnel(snapshot)
        self._render_trends(snapshot)
        self._render_workflows(snapshot)
        self._render_alerts(snapshot)
        if not self._options_loaded:
            self._load_options(snapshot)

    def _render_funnel(self, snapshot: DashboardSnapshot) -> None:
        while self.funnel_layout.count():
            item = self.funnel_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        populated = [stage for stage in snapshot.funnel if stage["count"]]
        if not populated:
            self.funnel_layout.addWidget(QLabel("Sem dados no período"))
            return
        maximum = max(int(stage["count"]) for stage in populated)
        for stage in populated:
            row = QWidget()
            layout = QHBoxLayout(row)
            layout.addWidget(QLabel(str(stage["stage"])))
            bar = QProgressBar()
            bar.setRange(0, maximum)
            bar.setValue(int(stage["count"]))
            bar.setFormat(f"{stage['count']} ({float(stage['conversion']):.1f}%)")
            layout.addWidget(bar)
            self.funnel_layout.addWidget(row)

    def _render_trends(self, snapshot: DashboardSnapshot) -> None:
        self.trend_table.setRowCount(len(snapshot.trends))
        for row_index, point in enumerate(snapshot.trends):
            for column, key in enumerate(("period", "jobs", "applications", "interviews", "offers")):
                self.trend_table.setItem(row_index, column, QTableWidgetItem(str(point[key])))

    def _render_workflows(self, snapshot: DashboardSnapshot) -> None:
        latest = snapshot.workflows["latest"]
        self.workflow_table.setRowCount(len(latest))
        for row_index, execution in enumerate(latest):
            for column, key in enumerate(("id", "workflow", "status", "created_at")):
                self.workflow_table.setItem(
                    row_index, column, QTableWidgetItem(str(execution[key]))
                )

    def _render_alerts(self, snapshot: DashboardSnapshot) -> None:
        self.alerts_list.clear()
        if not snapshot.alerts:
            self.alerts_list.addItem("Nenhum alerta operacional no período.")
        for alert in snapshot.alerts:
            self.alerts_list.addItem(f"{alert['count']} — {alert['message']}")

    def _load_options(self, snapshot: DashboardSnapshot) -> None:
        for company in snapshot.options["companies"]:
            self.company_combo.addItem(str(company["name"]), int(company["id"]))
        for status in snapshot.options["statuses"]:
            self.status_combo.addItem(str(status), str(status))
        for source in snapshot.options["sources"]:
            self.source_combo.addItem(str(source), str(source))
        self._options_loaded = True

    def _on_domain_event(self, _event_type: str, _payload: dict[str, Any]) -> None:
        self.refresh_requested.emit()
