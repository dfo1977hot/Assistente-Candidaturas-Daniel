from __future__ import annotations

from datetime import date
from pathlib import Path

from acd.services.analytics_service import AnalyticsFilters, DashboardSnapshot
from acd.ui.dashboard import Dashboard


class AnalyticsStub:
    PERIODS = ("7 dias", "30 dias", "90 dias", "Ano atual", "Todo o período", "Personalizado")

    def get_dashboard(self, filters=None):
        del filters
        return snapshot()


class EventBusStub:
    def __init__(self):
        self.handlers = {}

    def subscribe(self, event_type, handler):
        self.handlers[event_type] = handler


def snapshot(has_data=True):
    return DashboardSnapshot(
        kpis={
            "jobs_total": 2,
            "jobs_active": 1,
            "applications_total": 1,
            "applications_in_progress": 1,
            "interviews": 0,
            "offers": 0,
            "closed_or_rejected": 0,
            "application_to_interview_rate": 0.0,
            "interview_to_offer_rate": 0.0,
            "active_workflows": 1,
            "workflows_running": 0,
            "workflows_awaiting_user": 0,
            "recent_failures": 0,
            "next_scheduled_run": None,
            "cover_letters": 0,
            "optimized_resumes": 0,
        },
        funnel=(),
        trends=(),
        workflows={"latest": ()},
        alerts=(),
        options={
            "companies": ({"id": 1, "name": "ACME"},),
            "statuses": ("Aplicada",),
            "sources": ("LinkedIn",),
        },
        period_label="2026-08-01 a 2026-08-12",
        has_data=has_data,
    )


def test_dashboard_refresh_uses_long_running_executor_without_blocking(qapp, monkeypatch):
    dashboard = Dashboard(AnalyticsStub())
    captured = []
    monkeypatch.setattr(dashboard._executor, "execute", captured.append)

    dashboard.refresh_button.click()

    assert len(captured) == 1
    assert dashboard.refresh_button.text() == "Atualizar"


def test_dashboard_renders_empty_state_and_query_error(qapp, monkeypatch):
    dashboard = Dashboard(AnalyticsStub())
    dashboard._apply_snapshot(snapshot(has_data=False))
    monkeypatch.setattr("acd.ui.dashboard.QMessageBox.warning", lambda *args: None)

    assert dashboard.query_status.text() == "Sem dados no período"
    dashboard._on_error(RuntimeError("offline"))
    assert "Não foi possível" in dashboard.query_status.text()


def test_filters_and_event_refresh_are_connected(qapp, monkeypatch):
    bus = EventBusStub()
    dashboard = Dashboard(AnalyticsStub(), bus)
    calls = []
    monkeypatch.setattr(dashboard, "refresh_kpis", lambda: calls.append("refresh"))
    dashboard._apply_snapshot(snapshot())
    dashboard.period_combo.setCurrentText("Personalizado")
    dashboard.start_date.setDate(date(2026, 8, 1))
    dashboard.end_date.setDate(date(2026, 8, 12))

    selected = dashboard._selected_filters()
    bus.handlers["application.created"]("application.created", {})
    qapp.processEvents()

    assert isinstance(selected, AnalyticsFilters)
    assert selected.start_date == date(2026, 8, 1)
    assert selected.company_id is None
    assert calls == ["refresh"]


def test_dashboard_presentation_has_no_infrastructure_or_dependency_construction():
    source = (Path(__file__).parents[2] / "acd" / "ui" / "dashboard.py").read_text(encoding="utf-8")

    assert "acd.infrastructure" not in source
    assert "Repository(" not in source
    assert "Service(" not in source
    assert "LongRunningTaskExecutor(self)" in source


def test_dashboard_waits_for_active_query_during_shutdown(qapp, monkeypatch):
    dashboard = Dashboard(AnalyticsStub())
    events = []
    monkeypatch.setattr(type(dashboard._executor), "is_running", property(lambda self: True))
    monkeypatch.setattr(dashboard._executor, "cancel", lambda: events.append("cancel"))
    monkeypatch.setattr(
        dashboard._executor, "wait_for_finished", lambda: events.append("wait")
    )

    dashboard.close()

    assert events == ["cancel", "wait"]
