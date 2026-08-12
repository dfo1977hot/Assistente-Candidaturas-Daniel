from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
import json

import pytest

from acd.services.analytics_service import AnalyticsFilters, AnalyticsService
from acd.services.application_service import ApplicationService


class OperationalRepository:
    def __init__(self, data=None):
        self.data = data or empty_data()

    def load_operational_data(self):
        return self.data


def empty_data():
    return {
        "companies": [],
        "jobs": [],
        "applications": [],
        "workflows": [],
        "workflow_executions": [],
        "cover_letters": [],
        "resume_versions": [],
    }


def real_data(now: datetime):
    old = now - timedelta(days=200)
    schedule = {
        "trigger": "Agendado",
        "schedule": {
            "active": True,
            "next_run_at": (now - timedelta(hours=1)).isoformat(),
        },
    }
    return {
        "companies": [{"id": 1, "name": "ACME"}, {"id": 2, "name": "Beta"}],
        "jobs": [
            {"id": 1, "company_id": 1, "title": "Python", "status": "Nova", "source": "LinkedIn", "created_at": now, "updated_at": now},
            {"id": 2, "company_id": 2, "title": "Java", "status": "Encerrada", "source": "Site", "created_at": old, "updated_at": old},
            {"id": 3, "company_id": 1, "title": "Dados", "status": "Analisada", "source": "LinkedIn", "created_at": now, "updated_at": now},
        ],
        "applications": [
            {"id": 1, "job_id": 1, "company_id": 1, "status": "Entrevista RH", "application_channel": "LinkedIn", "created_at": now, "updated_at": now, "last_update": now.date()},
            {"id": 2, "job_id": 2, "company_id": 2, "status": "Oferta", "application_channel": "Site", "created_at": old, "updated_at": old, "last_update": old.date()},
            {"id": 3, "job_id": 1, "company_id": 1, "status": "Aplicada", "application_channel": "LinkedIn", "created_at": now, "updated_at": old, "last_update": old.date()},
            {"id": 4, "job_id": 1, "company_id": 1, "status": "Rejeitada", "application_channel": "LinkedIn", "created_at": now, "updated_at": now, "last_update": now.date()},
        ],
        "workflows": [{"id": 1, "name": "Preparar", "active": True, "definition": json.dumps(schedule)}],
        "workflow_executions": [
            {"id": 3, "workflow_id": 1, "status": "Aguardando usuário", "started_at": now, "finished_at": None, "created_at": now, "result": ""},
            {"id": 2, "workflow_id": 1, "status": "Falhou", "started_at": now, "finished_at": now, "created_at": now, "result": "erro"},
            {"id": 1, "workflow_id": 1, "status": "Em execução", "started_at": now, "finished_at": None, "created_at": now, "result": ""},
        ],
        "cover_letters": [{"id": 1, "created_at": now}],
        "resume_versions": [{"id": 1, "created_at": now}],
    }


def service(data):
    return AnalyticsService(repository=OperationalRepository(data))


def test_empty_database_returns_zero_kpis_and_empty_state():
    snapshot = service(empty_data()).get_dashboard(AnalyticsFilters(period="Todo o período"))

    assert snapshot.has_data is False
    assert snapshot.kpis["jobs_total"] == 0
    assert snapshot.kpis["applications_total"] == 0
    assert snapshot.kpis["application_to_interview_rate"] == 0
    assert snapshot.kpis["interview_to_offer_rate"] == 0


def test_real_kpis_rates_workflows_and_trustworthy_generated_counts():
    now = datetime(2026, 8, 12, 12, tzinfo=UTC)
    snapshot = service(real_data(now)).get_dashboard(
        AnalyticsFilters(period="Todo o período"), now=now
    )

    assert snapshot.kpis["jobs_total"] == 3
    assert snapshot.kpis["jobs_active"] == 2
    assert snapshot.kpis["applications_total"] == 4
    assert snapshot.kpis["interviews"] == 2
    assert snapshot.kpis["offers"] == 1
    assert snapshot.kpis["application_to_interview_rate"] == 50
    assert snapshot.kpis["interview_to_offer_rate"] == 50
    assert snapshot.kpis["cover_letters"] == 1
    assert snapshot.kpis["optimized_resumes"] == 1
    assert snapshot.workflows["running"] == 1
    assert snapshot.workflows["awaiting_user"] == 1
    assert snapshot.workflows["recent_failures"] == 1
    assert snapshot.workflows["next_scheduled_run"] is not None


def test_funnel_contains_only_real_application_statuses():
    now = datetime(2026, 8, 12, 12, tzinfo=UTC)
    funnel = service(real_data(now)).get_dashboard(
        AnalyticsFilters(period="Todo o período"), now=now
    ).funnel

    assert {item["stage"] for item in funnel} == set(ApplicationService.VALID_STATUSES)
    assert next(item for item in funnel if item["stage"] == "Oferta")["count"] == 1


@pytest.mark.parametrize(
    ("filters", "expected"),
    [
        (AnalyticsFilters(period="7 dias"), 3),
        (AnalyticsFilters(period="Todo o período", company_id=2), 1),
        (AnalyticsFilters(period="Todo o período", application_status="Oferta"), 1),
        (AnalyticsFilters(period="Todo o período", source="Site"), 1),
        (AnalyticsFilters(period="Todo o período", text="Python"), 3),
    ],
)
def test_period_company_status_source_and_text_filters(filters, expected):
    now = datetime(2026, 8, 12, 12, tzinfo=UTC)
    snapshot = service(real_data(now)).get_dashboard(filters, now=now)

    assert snapshot.kpis["applications_total"] == expected


def test_custom_period_validation():
    with pytest.raises(ValueError, match="data inicial"):
        service(empty_data()).get_dashboard(
            AnalyticsFilters(
                period="Personalizado",
                start_date=date(2026, 8, 12),
                end_date=date(2026, 8, 1),
            )
        )


def test_short_and_long_periods_select_daily_and_monthly_trends():
    now = datetime(2026, 8, 12, 12, tzinfo=UTC)
    short = service(real_data(now)).get_dashboard(AnalyticsFilters(period="7 dias"), now=now)
    long = service(real_data(now)).get_dashboard(AnalyticsFilters(period="Todo o período"), now=now)

    assert {point["granularity"] for point in short.trends} == {"diária"}
    assert {point["granularity"] for point in long.trends} == {"mensal"}


def test_operational_alerts_use_centralized_limits_and_real_state():
    now = datetime(2026, 8, 12, 12, tzinfo=UTC)
    alerts = service(real_data(now)).get_dashboard(
        AnalyticsFilters(period="Todo o período"), now=now
    ).alerts

    kinds = {alert["type"] for alert in alerts}
    assert {"awaiting_user", "workflow_failure", "stale_application", "pending_application", "overdue_schedule"} <= kinds
    assert AnalyticsService.STALE_APPLICATION_DAYS == 14
