from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Protocol

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from acd.presentation.long_running_task_executor import LongRunningTaskExecutor
from acd.presentation.pages.base_page import BasePage
from acd.services.analytics_service import (
    AnalyticsFilters,
    AnalyticsRecord,
    DashboardSnapshot,
)
from acd.ui.widgets.kpi_card import KPICard


class AnalyticsGateway(Protocol):
    PERIODS: tuple[str, ...]

    def get_dashboard(self, filters: AnalyticsFilters | None = None) -> DashboardSnapshot: ...


class EventGateway(Protocol):
    def subscribe(self, event_type: str, handler: Any) -> None: ...


class ExportGateway(Protocol):
    def safe_filename(self, label: str, extension: str) -> str: ...
    def export_csv(self, records: Sequence[AnalyticsRecord], destination: str | Path, **kwargs: Any) -> Path: ...
    def export_xlsx(self, records: Sequence[AnalyticsRecord], destination: str | Path, **kwargs: Any) -> Path: ...


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
        export_service: ExportGateway | None = None,
        navigate_to_record: Callable[[str, int], None] | None = None,
    ) -> None:
        super().__init__("Dashboard")
        self.analytics_service = analytics_service
        self.export_service = export_service
        self._navigate_to_record = navigate_to_record
        self._executor = LongRunningTaskExecutor(self)
        self._export_executor = LongRunningTaskExecutor(self)
        self._snapshot: DashboardSnapshot | None = None
        self._loaded_once = False
        self._options_loaded = False
        self._build_filters()
        self._build_kpis()
        self._build_views()
        self._build_export_controls()
        self._executor.started.connect(self._on_loading)
        self._executor.succeeded.connect(self._apply_snapshot)
        self._executor.failed.connect(self._on_error)
        self._executor.finished.connect(self._on_finished)
        self._export_executor.started.connect(self._on_export_started)
        self._export_executor.progress.connect(self._on_export_progress)
        self._export_executor.succeeded.connect(self._on_export_succeeded)
        self._export_executor.failed.connect(self._on_export_failed)
        self._export_executor.cancelled.connect(self._on_export_cancelled)
        self._export_executor.finished.connect(self._on_export_finished)
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
        self.clear_filters_button = QPushButton("Limpar filtros")
        self.refresh_button.clicked.connect(self.refresh_kpis)
        self.clear_filters_button.clicked.connect(self.clear_filters)
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
        row.addWidget(self.clear_filters_button)
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
        for key, card in self.kpi_cards.items():
            if key in {
                "jobs_total", "jobs_active", "applications_total", "applications_in_progress",
                "interviews", "offers", "closed_or_rejected", "workflows_awaiting_user",
                "recent_failures", "cover_letters",
            }:
                card.setCursor(Qt.PointingHandCursor)
                card.clicked.connect(lambda key=key: self.open_drilldown(key))
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
        self.view_stack = QStackedWidget()
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
        body_layout.addWidget(QLabel("Tabela analítica"))
        self.analytics_table = QTableWidget(0, 12)
        self.analytics_table.setHorizontalHeaderLabels(
            ["Empresa", "Cargo", "Origem", "Status", "Criação", "Atualização",
             "Remuneração oferecida", "Remuneração ideal", "Fit score", "Currículo",
             "Carta", "Workflow"]
        )
        self.analytics_table.cellDoubleClicked.connect(self._open_analytics_record)
        body_layout.addWidget(self.analytics_table)
        scroll.setWidget(body)
        self.main_view = scroll
        self.view_stack.addWidget(self.main_view)

        self.detail_view = QWidget()
        detail_layout = QVBoxLayout(self.detail_view)
        detail_header = QHBoxLayout()
        self.back_button = QPushButton("Voltar")
        self.back_button.clicked.connect(lambda: self.view_stack.setCurrentWidget(self.main_view))
        self.detail_title = QLabel("Detalhes")
        self.detail_count = QLabel("0 registros")
        detail_header.addWidget(self.back_button)
        detail_header.addWidget(self.detail_title)
        detail_header.addStretch(1)
        detail_header.addWidget(self.detail_count)
        detail_layout.addLayout(detail_header)
        self.detail_table = QTableWidget(0, 7)
        self.detail_table.setHorizontalHeaderLabels(
            ["Tipo", "ID", "Empresa", "Cargo/Workflow", "Status", "Data", "Origem"]
        )
        self.detail_table.cellDoubleClicked.connect(self._open_detail_record)
        detail_layout.addWidget(self.detail_table)
        self.view_stack.addWidget(self.detail_view)
        self.layout.addWidget(self.view_stack)

    def _build_export_controls(self) -> None:
        row = QHBoxLayout()
        self.export_csv_button = QPushButton("Exportar CSV")
        self.export_xlsx_button = QPushButton("Exportar Excel")
        self.cancel_export_button = QPushButton("Cancelar exportação")
        self.cancel_export_button.setEnabled(False)
        self.export_progress = QProgressBar()
        self.export_progress.setRange(0, 100)
        self.export_progress.setValue(0)
        self.export_csv_button.clicked.connect(lambda: self._choose_export("csv"))
        self.export_xlsx_button.clicked.connect(lambda: self._choose_export("xlsx"))
        self.cancel_export_button.clicked.connect(self._export_executor.cancel)
        for widget in (
            self.export_csv_button, self.export_xlsx_button,
            self.cancel_export_button, self.export_progress,
        ):
            row.addWidget(widget)
        self.layout.addLayout(row)

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
        if self._export_executor.is_running:
            self._export_executor.cancel()
            self._export_executor.wait_for_finished()

    def clear_filters(self) -> None:
        self.period_combo.setCurrentText("30 dias")
        self.start_date.setDate(QDate.currentDate().addDays(-29))
        self.end_date.setDate(QDate.currentDate())
        self.company_combo.setCurrentIndex(0)
        self.text_filter.clear()
        self.status_combo.setCurrentIndex(0)
        self.source_combo.setCurrentIndex(0)
        self.view_stack.setCurrentWidget(self.main_view)
        self.refresh_kpis()

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
        self._snapshot = snapshot
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
        self._render_analytics(snapshot.records)
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
        for stage in populated:
            row = QWidget()
            layout = QHBoxLayout(row)
            layout.addWidget(QLabel(str(stage["stage"])))
            detail_button = QPushButton(
                f"{stage['count']} ({float(stage['conversion']):.1f}%)"
            )
            detail_button.clicked.connect(
                lambda _checked=False, status=str(stage["stage"]): self.open_drilldown(
                    f"funnel:{status}"
                )
            )
            layout.addWidget(detail_button)
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

    def _render_analytics(self, records: Sequence[AnalyticsRecord]) -> None:
        self.analytics_table.setRowCount(len(records))
        for row_index, record in enumerate(records):
            values = (
                record.company, record.title, record.source, record.application_status,
                record.created_at.strftime("%d/%m/%Y %H:%M"),
                record.updated_at.strftime("%d/%m/%Y %H:%M"),
                self._money(record.salary_offered), self._money(record.salary_ideal),
                "" if record.fit_score is None else f"{record.fit_score:.1f}",
                record.curriculum, record.cover_letter, record.workflow_status,
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setData(Qt.UserRole, ("application", record.application_id))
                self.analytics_table.setItem(row_index, column, item)
        self.analytics_table.resizeColumnsToContents()

    def open_drilldown(self, key: str) -> None:
        if self._snapshot is None:
            return
        items = self._snapshot.drilldowns.get(key, ())
        self.detail_title.setText(self.kpi_cards[key].title_label.text() if key in self.kpi_cards else key.removeprefix("funnel:"))
        self.detail_count.setText(f"{len(items)} registros")
        self.detail_table.setRowCount(len(items))
        for row_index, item in enumerate(items):
            values = (
                item.entity_type, item.entity_id, item.company, item.title, item.status,
                item.relevant_date.strftime("%d/%m/%Y %H:%M"), item.source,
            )
            for column, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                cell.setData(Qt.UserRole, (item.entity_type, item.entity_id))
                self.detail_table.setItem(row_index, column, cell)
        self.detail_table.resizeColumnsToContents()
        self.view_stack.setCurrentWidget(self.detail_view)

    def _open_analytics_record(self, row: int, _column: int) -> None:
        self._navigate_from_item(self.analytics_table.item(row, 0))

    def _open_detail_record(self, row: int, _column: int) -> None:
        self._navigate_from_item(self.detail_table.item(row, 0))

    def _navigate_from_item(self, item: QTableWidgetItem | None) -> None:
        if item is None or self._navigate_to_record is None:
            return
        entity_type, entity_id = item.data(Qt.UserRole)
        self._navigate_to_record(str(entity_type), int(entity_id))

    def _choose_export(self, format_name: str) -> None:
        if self.export_service is None or self._snapshot is None:
            return
        extension = "csv" if format_name == "csv" else "xlsx"
        suggested = self.export_service.safe_filename(self._snapshot.period_label, extension)
        destination, _ = QFileDialog.getSaveFileName(
            self, "Exportar Analytics", suggested,
            "CSV (*.csv)" if format_name == "csv" else "Excel (*.xlsx)",
        )
        if destination:
            self.start_export(format_name, Path(destination))

    def start_export(self, format_name: str, destination: Path) -> None:
        if self.export_service is None or self._snapshot is None or self._export_executor.is_running:
            return
        records = self._snapshot.records

        def export(progress: Callable[[object], None], cancellation: object) -> tuple[str, Path]:
            method = (
                self.export_service.export_csv
                if format_name == "csv"
                else self.export_service.export_xlsx
            )
            path = method(records, destination, progress=progress, cancellation=cancellation)
            return format_name, path

        self._export_executor.execute_with_context(export)

    def _on_export_started(self) -> None:
        self.export_csv_button.setEnabled(False)
        self.export_xlsx_button.setEnabled(False)
        self.cancel_export_button.setEnabled(True)
        self.export_progress.setValue(0)
        self.query_status.setText("Exportando dados filtrados…")

    def _on_export_progress(self, payload: object) -> None:
        if isinstance(payload, dict):
            self.export_progress.setValue(int(payload.get("percent", 0)))

    def _on_export_succeeded(self, result: object) -> None:
        _format_name, path = result
        self.export_progress.setValue(100)
        self.query_status.setText(f"Exportação concluída: {path}")

    def _on_export_failed(self, error: object) -> None:
        self.query_status.setText("Não foi possível exportar os dados.")
        QMessageBox.warning(self, "Exportação", f"Erro ao gravar arquivo: {error}")

    def _on_export_cancelled(self) -> None:
        self.query_status.setText("Exportação cancelada.")

    def _on_export_finished(self) -> None:
        self.export_csv_button.setEnabled(True)
        self.export_xlsx_button.setEnabled(True)
        self.cancel_export_button.setEnabled(False)

    @staticmethod
    def _money(value: float | None) -> str:
        return "A combinar" if value is None else f"R$ {value:,.2f}"

    def _on_domain_event(self, _event_type: str, _payload: dict[str, Any]) -> None:
        self.refresh_requested.emit()
