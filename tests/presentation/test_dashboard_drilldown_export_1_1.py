from __future__ import annotations

from datetime import datetime
from pathlib import Path

from acd.services.analytics_service import AnalyticsRecord, DrilldownItem
from acd.ui.dashboard import Dashboard
from tests.presentation.test_dashboard_analytics_page_1_0 import AnalyticsStub, snapshot


class ExportStub:
    def safe_filename(self, label, extension):
        return f"safe.{extension}"

    def export_csv(self, records, destination, **kwargs):
        return destination

    def export_xlsx(self, records, destination, **kwargs):
        return destination


def detailed_snapshot():
    base = snapshot()
    now = datetime(2026, 8, 12, 12)
    record = AnalyticsRecord(
        1, 2, 3, "ACME", "Python", "LinkedIn", "Aplicada", now, now,
        8000, 10000, 90, "CV", "Carta #1", "Concluída",
    )
    item = DrilldownItem("application", 1, 2, "ACME", "Python", "Aplicada", now, "LinkedIn")
    return type(base)(
        kpis=base.kpis, funnel=base.funnel, trends=base.trends,
        workflows=base.workflows, alerts=base.alerts, options=base.options,
        period_label=base.period_label, has_data=True, records=(record,),
        drilldowns={"applications_total": (item,), "funnel:Aplicada": (item,)},
    )


def test_kpi_drilldown_and_back_preserve_filter_widgets(qapp):
    dashboard = Dashboard(AnalyticsStub(), export_service=ExportStub())
    dashboard._apply_snapshot(detailed_snapshot())
    dashboard.text_filter.setText("Python")

    dashboard.open_drilldown("applications_total")
    assert dashboard.detail_table.rowCount() == 1
    assert dashboard.detail_count.text() == "1 registros"
    dashboard.back_button.click()

    assert dashboard.text_filter.text() == "Python"
    assert dashboard.view_stack.currentWidget() is dashboard.main_view


def test_analytical_table_and_indirect_navigation(qapp):
    calls = []
    dashboard = Dashboard(
        AnalyticsStub(), export_service=ExportStub(), navigate_to_record=lambda *args: calls.append(args)
    )
    dashboard._apply_snapshot(detailed_snapshot())

    assert dashboard.analytics_table.rowCount() == 1
    assert dashboard.analytics_table.columnCount() == 12
    dashboard._open_analytics_record(0, 0)
    assert calls == [("application", 1)]


def test_export_runs_through_context_executor_and_restores_controls(qapp, monkeypatch, tmp_path):
    dashboard = Dashboard(AnalyticsStub(), export_service=ExportStub())
    dashboard._apply_snapshot(detailed_snapshot())
    captured = []
    monkeypatch.setattr(dashboard._export_executor, "execute_with_context", captured.append)

    dashboard.start_export("csv", tmp_path / "analytics.csv")
    assert len(captured) == 1
    dashboard._on_export_started()
    assert not dashboard.export_csv_button.isEnabled()
    assert dashboard.cancel_export_button.isEnabled()
    dashboard._on_export_progress({"percent": 65})
    assert dashboard.export_progress.value() == 65
    dashboard._on_export_finished()
    assert dashboard.export_csv_button.isEnabled()
    assert not dashboard.cancel_export_button.isEnabled()


def test_clear_filters_restores_defaults_without_concrete_page_dependency(qapp, monkeypatch):
    dashboard = Dashboard(AnalyticsStub(), export_service=ExportStub())
    dashboard._apply_snapshot(detailed_snapshot())
    dashboard.text_filter.setText("Python")
    monkeypatch.setattr(dashboard, "refresh_kpis", lambda: None)

    dashboard.clear_filters()

    assert dashboard.text_filter.text() == ""
    assert dashboard.period_combo.currentText() == "30 dias"
    source = (Path(__file__).parents[2] / "acd" / "ui" / "dashboard.py").read_text(encoding="utf-8")
    assert "ApplicationPage" not in source
    assert "JobPage" not in source
    assert "acd.infrastructure" not in source


def test_composition_root_injects_export_and_indirect_navigation():
    source = (Path(__file__).parents[2] / "acd" / "desktop_composition_root.py").read_text(
        encoding="utf-8"
    )

    assert "analytics_export_service = AnalyticsExportService()" in source
    assert "navigate_to_analytics_record" in source
    assert "Dashboard(" in source
