from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime, timedelta
import json
from typing import Any

from acd.infrastructure.repositories.analytics_repository import AnalyticsRepository
from acd.services.application_service import ApplicationService
from acd.services.metrics_engine import MetricsEngine
from acd.services.recommendation_engine import RecommendationEngine
from acd.services.trend_analysis_service import TrendAnalysisService


@dataclass(frozen=True, slots=True)
class AnalyticsFilters:
    """Serializable filters accepted by every operational aggregation."""

    period: str = "30 dias"
    start_date: date | None = None
    end_date: date | None = None
    company_id: int | None = None
    text: str = ""
    application_status: str = ""
    source: str = ""


@dataclass(frozen=True, slots=True)
class DashboardSnapshot:
    """Immutable, serializable result consumed by the dashboard Presentation."""

    kpis: dict[str, int | float | str | None]
    funnel: tuple[dict[str, int | float | str], ...]
    trends: tuple[dict[str, int | str], ...]
    workflows: dict[str, Any]
    alerts: tuple[dict[str, str | int], ...]
    options: dict[str, tuple[dict[str, int | str] | str, ...]]
    period_label: str
    has_data: bool
    records: tuple[AnalyticsRecord, ...] = ()
    drilldowns: dict[str, tuple[DrilldownItem, ...]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AnalyticsRecord:
    """Compact application projection for tables and exports; no large text fields."""

    application_id: int
    job_id: int
    company_id: int
    company: str
    title: str
    source: str
    application_status: str
    created_at: datetime
    updated_at: datetime
    salary_offered: float | None
    salary_ideal: float | None
    fit_score: float | None
    curriculum: str
    cover_letter: str
    workflow_status: str


@dataclass(frozen=True, slots=True)
class DrilldownItem:
    """Navigation-safe row for KPI and funnel detail lists."""

    entity_type: str
    entity_id: int
    related_id: int | None
    company: str
    title: str
    status: str
    relevant_date: datetime
    source: str


class AnalyticsService:
    """Centralize operational filters and aggregations over real ACD data."""

    PERIODS = ("7 dias", "30 dias", "90 dias", "Ano atual", "Todo o período", "Personalizado")
    STALE_APPLICATION_DAYS = 14
    RECENT_FAILURE_DAYS = 7
    TERMINAL_APPLICATION_STATUSES = frozenset({"Contratada", "Rejeitada", "Encerrada"})
    INTERVIEW_STATUSES = frozenset(
        {"Entrevista RH", "Teste", "Entrevista Técnica", "Entrevista Gestor", "Oferta", "Contratada"}
    )
    OFFER_STATUSES = frozenset({"Oferta", "Contratada"})
    CLOSED_JOB_STATUSES = frozenset({"Rejeitada", "Encerrada"})

    def __init__(
        self,
        repository: AnalyticsRepository | None = None,
        metrics_engine: MetricsEngine | None = None,
        recommendation_engine: RecommendationEngine | None = None,
        trend_service: TrendAnalysisService | None = None,
    ) -> None:
        self.repository = repository or AnalyticsRepository()
        self.metrics_engine = metrics_engine or MetricsEngine()
        self.recommendation_engine = recommendation_engine or RecommendationEngine(
            self.repository, self.metrics_engine
        )
        self.trend_service = trend_service or TrendAnalysisService(
            self.repository, self.metrics_engine
        )

    def get_dashboard(
        self,
        filters: AnalyticsFilters | None = None,
        *,
        now: datetime | None = None,
    ) -> DashboardSnapshot:
        """Build the complete operational dashboard from one compact repository read."""
        selected = filters or AnalyticsFilters()
        current = self._naive(now or datetime.now(UTC))
        rows = self.repository.load_operational_data()
        start, end = self._date_range(selected, current.date())
        jobs = self._filter_jobs(rows["jobs"], selected, start, end)
        job_ids = {row["id"] for row in jobs}
        applications = self._filter_applications(
            rows["applications"], selected, start, end, job_ids
        )
        executions = self._within_period(rows["workflow_executions"], "created_at", start, end)
        letters = self._within_period(rows["cover_letters"], "created_at", start, end)
        resumes = self._within_period(rows["resume_versions"], "created_at", start, end)
        schedules = self._schedules(rows["workflows"])

        interview_count = sum(row["status"] in self.INTERVIEW_STATUSES for row in applications)
        offer_count = sum(row["status"] in self.OFFER_STATUSES for row in applications)
        total_applications = len(applications)
        kpis: dict[str, int | float | str | None] = {
            "jobs_total": len(jobs),
            "jobs_active": sum(row["status"] not in self.CLOSED_JOB_STATUSES for row in jobs),
            "applications_total": total_applications,
            "applications_in_progress": sum(
                row["status"] not in self.TERMINAL_APPLICATION_STATUSES for row in applications
            ),
            "interviews": interview_count,
            "offers": offer_count,
            "closed_or_rejected": sum(
                row["status"] in {"Rejeitada", "Encerrada"} for row in applications
            ),
            "application_to_interview_rate": self._rate(interview_count, total_applications),
            "interview_to_offer_rate": self._rate(offer_count, interview_count),
            "active_workflows": sum(bool(row["active"]) for row in rows["workflows"]),
            "workflows_running": sum(row["status"] == "Em execução" for row in executions),
            "workflows_awaiting_user": sum(
                row["status"] == "Aguardando usuário" for row in executions
            ),
            "recent_failures": sum(
                row["status"] == "Falhou"
                and self._naive(row["created_at"]) >= current - timedelta(days=self.RECENT_FAILURE_DAYS)
                for row in executions
            ),
            "next_scheduled_run": self._next_run(schedules, current),
            "cover_letters": len(letters),
            "optimized_resumes": len(resumes),
        }
        funnel = self._funnel(applications)
        trends = self._trends(jobs, applications, start, end, current.date())
        workflows = self._workflow_summary(executions, rows["workflows"], schedules, current)
        alerts = self._alerts(
            applications, jobs, rows["workflow_executions"], schedules, current
        )
        options = self._options(rows)
        records = self._records(rows, applications)
        drilldowns = self._drilldowns(
            jobs, applications, executions, letters, rows, records, current
        )
        return DashboardSnapshot(
            kpis=kpis,
            funnel=tuple(funnel),
            trends=tuple(trends),
            workflows=workflows,
            alerts=tuple(alerts),
            options=options,
            period_label=self._period_label(start, end),
            has_data=bool(jobs or applications or executions or letters or resumes),
            records=tuple(records),
            drilldowns=drilldowns,
        )

    def get_filtered_records(
        self, filters: AnalyticsFilters | None = None
    ) -> tuple[AnalyticsRecord, ...]:
        """Return the same filtered projection used by Dashboard drill-down/export."""
        return self.get_dashboard(filters).records

    def calculate_kpis(self) -> dict[str, Any]:
        """Preserve the established analytics API while using operational data."""
        operational = self.get_dashboard(AnalyticsFilters(period="Todo o período")).kpis
        return {
            **operational,
            "conversion_to_interview": f"{operational['application_to_interview_rate']:.1f}%",
            "average_ats": "N/D",
            "best_platform": "N/D",
            "total_applications": operational["applications_total"],
            "interviews_scheduled": operational["interviews"],
            "offers_received": operational["offers"],
        }

    def generate_dashboard(self) -> dict[str, Any]:
        snapshot = self.get_dashboard(AnalyticsFilters(period="Todo o período"))
        return {
            **snapshot.to_dict(),
            "metrics": snapshot.kpis,
            "operational_trends": snapshot.trends,
            "trends": self.trend_service.get_all_trends(),
            "recommendations": self.get_recommendations(),
        }

    def get_conversion_funnel(self) -> list[dict[str, Any]]:
        return list(self.get_dashboard(AnalyticsFilters(period="Todo o período")).funnel)

    def get_recommendations(self) -> list[dict[str, Any]]:
        return self.recommendation_engine.generate_recommendations()

    def create_snapshot(self, period: str = "daily") -> dict[str, Any]:
        dashboard = self.generate_dashboard()
        kpis = json.dumps(dashboard["kpis"], ensure_ascii=False, default=str)
        snapshot = self.repository.create_snapshot(period, kpis, kpis)
        return {"id": snapshot.id, "period": snapshot.period, "created_at": str(snapshot.created_at)}

    @classmethod
    def _date_range(
        cls, filters: AnalyticsFilters, today: date
    ) -> tuple[date | None, date | None]:
        if filters.period == "Todo o período":
            return None, None
        if filters.period == "Personalizado":
            if filters.start_date and filters.end_date and filters.start_date > filters.end_date:
                raise ValueError("A data inicial não pode ser posterior à data final.")
            return filters.start_date, filters.end_date
        if filters.period == "Ano atual":
            return date(today.year, 1, 1), today
        days = {"7 dias": 7, "30 dias": 30, "90 dias": 90}.get(filters.period, 30)
        return today - timedelta(days=days - 1), today

    @classmethod
    def _filter_jobs(
        cls,
        rows: list[dict[str, object]],
        filters: AnalyticsFilters,
        start: date | None,
        end: date | None,
    ) -> list[dict[str, object]]:
        text = filters.text.strip().casefold()
        return [
            row
            for row in cls._within_period(rows, "created_at", start, end)
            if (filters.company_id is None or row["company_id"] == filters.company_id)
            and (not text or text in str(row["title"] or "").casefold())
            and (not filters.source or str(row["source"] or "") == filters.source)
        ]

    @classmethod
    def _filter_applications(
        cls,
        rows: list[dict[str, object]],
        filters: AnalyticsFilters,
        start: date | None,
        end: date | None,
        matching_job_ids: set[object],
    ) -> list[dict[str, object]]:
        return [
            row
            for row in cls._within_period(rows, "created_at", start, end)
            if (filters.company_id is None or row["company_id"] == filters.company_id)
            and (not filters.text.strip() or row["job_id"] in matching_job_ids)
            and (
                not filters.application_status
                or row["status"] == filters.application_status
            )
            and (
                not filters.source
                or str(row["application_channel"] or "") == filters.source
                or row["job_id"] in matching_job_ids
            )
        ]

    @classmethod
    def _within_period(
        cls,
        rows: list[dict[str, object]],
        field: str,
        start: date | None,
        end: date | None,
    ) -> list[dict[str, object]]:
        result = []
        for row in rows:
            value = row.get(field)
            if value is None:
                continue
            day = cls._naive(value).date()
            if (start is None or day >= start) and (end is None or day <= end):
                result.append(row)
        return result

    @classmethod
    def _funnel(cls, applications: list[dict[str, object]]) -> list[dict[str, Any]]:
        counts = Counter(str(row["status"]) for row in applications)
        previous = len(applications)
        result = []
        for status in ApplicationService.VALID_STATUS_TRANSITIONS:
            count = counts.get(status, 0)
            result.append(
                {"stage": status, "count": count, "conversion": cls._rate(count, previous)}
            )
            if count:
                previous = count
        return result

    @classmethod
    def _trends(
        cls,
        jobs: list[dict[str, object]],
        applications: list[dict[str, object]],
        start: date | None,
        end: date | None,
        today: date,
    ) -> list[dict[str, int | str]]:
        effective_start = start or min(
            [cls._naive(row["created_at"]).date() for row in jobs + applications] or [today]
        )
        effective_end = end or today
        span = max(1, (effective_end - effective_start).days + 1)
        granularity = "diária" if span <= 31 else "semanal" if span <= 120 else "mensal"
        buckets: dict[str, Counter[str]] = defaultdict(Counter)
        for row in jobs:
            buckets[cls._bucket(cls._naive(row["created_at"]).date(), granularity)]["jobs"] += 1
        for row in applications:
            created = cls._bucket(cls._naive(row["created_at"]).date(), granularity)
            buckets[created]["applications"] += 1
            milestone = cls._bucket(cls._naive(row["updated_at"]).date(), granularity)
            if row["status"] in cls.INTERVIEW_STATUSES:
                buckets[milestone]["interviews"] += 1
            if row["status"] in cls.OFFER_STATUSES:
                buckets[milestone]["offers"] += 1
        return [
            {
                "period": period,
                "jobs": values["jobs"],
                "applications": values["applications"],
                "interviews": values["interviews"],
                "offers": values["offers"],
                "granularity": granularity,
            }
            for period, values in sorted(buckets.items())
        ]

    @staticmethod
    def _bucket(value: date, granularity: str) -> str:
        if granularity == "diária":
            return value.isoformat()
        if granularity == "semanal":
            year, week, _ = value.isocalendar()
            return f"{year}-S{week:02d}"
        return value.strftime("%Y-%m")

    @classmethod
    def _workflow_summary(
        cls,
        executions: list[dict[str, object]],
        workflows: list[dict[str, object]],
        schedules: list[dict[str, object]],
        current: datetime,
    ) -> dict[str, Any]:
        today = current.date()
        names = {row["id"]: row["name"] for row in workflows}
        latest = sorted(executions, key=lambda row: row["id"], reverse=True)[:10]
        return {
            "executions_today": sum(cls._naive(row["created_at"]).date() == today for row in executions),
            "running": sum(row["status"] == "Em execução" for row in executions),
            "awaiting_user": sum(row["status"] == "Aguardando usuário" for row in executions),
            "recent_failures": sum(row["status"] == "Falhou" for row in executions),
            "next_scheduled_run": cls._next_run(schedules, current),
            "latest": tuple(
                {
                    "id": int(row["id"]),
                    "workflow": str(names.get(row["workflow_id"], f"Workflow {row['workflow_id']}")),
                    "status": str(row["status"]),
                    "created_at": cls._naive(row["created_at"]).isoformat(sep=" ", timespec="minutes"),
                }
                for row in latest
            ),
        }

    @classmethod
    def _alerts(
        cls,
        applications: list[dict[str, object]],
        jobs: list[dict[str, object]],
        executions: list[dict[str, object]],
        schedules: list[dict[str, object]],
        current: datetime,
    ) -> list[dict[str, str | int]]:
        alerts: list[dict[str, str | int]] = []
        awaiting = sum(row["status"] == "Aguardando usuário" for row in executions)
        failures = sum(
            row["status"] == "Falhou"
            and cls._naive(row["created_at"]) >= current - timedelta(days=cls.RECENT_FAILURE_DAYS)
            for row in executions
        )
        stale_limit = current.date() - timedelta(days=cls.STALE_APPLICATION_DAYS)
        stale = sum(
            row["status"] not in cls.TERMINAL_APPLICATION_STATUSES
            and (row["last_update"] or cls._naive(row["updated_at"]).date()) < stale_limit
            for row in applications
        )
        application_job_ids = {row["job_id"] for row in applications}
        pending_jobs = sum(
            row["status"] not in cls.CLOSED_JOB_STATUSES and row["id"] not in application_job_ids
            for row in jobs
        )
        overdue = sum(
            bool(item.get("active"))
            and item.get("next_run_at") is not None
            and cls._parse_datetime(item["next_run_at"]) < current
            for item in schedules
        )
        for kind, count, message in (
            ("awaiting_user", awaiting, "Workflows aguardando intervenção do usuário"),
            ("workflow_failure", failures, "Falhas de workflow nos últimos 7 dias"),
            ("stale_application", stale, f"Candidaturas sem atualização há {cls.STALE_APPLICATION_DAYS} dias"),
            ("pending_application", pending_jobs, "Vagas ativas sem candidatura"),
            ("overdue_schedule", overdue, "Agendamentos de workflow vencidos"),
        ):
            if count:
                alerts.append({"type": kind, "count": count, "message": message})
        return alerts

    @classmethod
    def _schedules(cls, workflows: list[dict[str, object]]) -> list[dict[str, object]]:
        schedules = []
        for row in workflows:
            try:
                definition = json.loads(str(row["definition"] or "{}"))
            except (TypeError, ValueError, json.JSONDecodeError):
                continue
            schedule = definition.get("schedule")
            if row["active"] and definition.get("trigger") == "Agendado" and isinstance(schedule, dict):
                schedules.append({"workflow_id": row["id"], **schedule})
        return schedules

    @classmethod
    def _next_run(cls, schedules: list[dict[str, object]], current: datetime) -> str | None:
        values = [
            cls._parse_datetime(item["next_run_at"])
            for item in schedules
            if item.get("active", True) and item.get("next_run_at")
        ]
        if not values:
            return None
        value = min(values)
        return value.isoformat(sep=" ", timespec="minutes")

    @classmethod
    def _options(cls, rows: dict[str, list[dict[str, object]]]) -> dict[str, tuple[Any, ...]]:
        companies = tuple(
            {"id": int(row["id"]), "name": str(row["name"])}
            for row in sorted(rows["companies"], key=lambda item: str(item["name"]).casefold())
        )
        sources = tuple(
            sorted(
                {
                    str(value).strip()
                    for row in rows["jobs"] + rows["applications"]
                    for value in (row.get("source"), row.get("application_channel"))
                    if value and str(value).strip()
                },
                key=str.casefold,
            )
        )
        return {
            "companies": companies,
            "statuses": tuple(ApplicationService.VALID_STATUS_TRANSITIONS),
            "sources": sources,
        }

    @classmethod
    def _records(
        cls,
        rows: dict[str, list[dict[str, object]]],
        applications: list[dict[str, object]],
    ) -> list[AnalyticsRecord]:
        companies = {row["id"]: str(row["name"]) for row in rows.get("companies", [])}
        jobs = {row["id"]: row for row in rows.get("jobs", [])}
        curricula = {row["id"]: str(row["name"]) for row in rows.get("curricula", [])}
        latest_scores: dict[object, dict[str, object]] = {}
        for score in rows.get("ats_scores", []):
            application_id = score.get("application_id")
            previous = latest_scores.get(application_id)
            if previous is None or score["calculated_at"] > previous["calculated_at"]:
                latest_scores[application_id] = score
        letters_by_application = {
            row.get("application_id"): row["id"]
            for row in rows.get("cover_letters", [])
            if row.get("application_id") is not None
        }
        workflow_by_application: dict[object, dict[str, object]] = {}
        for execution in sorted(
            rows.get("workflow_executions", []), key=lambda item: int(item["id"])
        ):
            if execution.get("application_id") is not None:
                workflow_by_application[execution["application_id"]] = execution
        result = []
        for application in applications:
            job = jobs.get(application["job_id"], {})
            score = latest_scores.get(application["id"])
            workflow = workflow_by_application.get(application["id"])
            letter_id = application.get("cover_letter_id") or letters_by_application.get(
                application["id"]
            )
            result.append(
                AnalyticsRecord(
                    application_id=int(application["id"]),
                    job_id=int(application["job_id"]),
                    company_id=int(application["company_id"]),
                    company=companies.get(application["company_id"], ""),
                    title=str(job.get("title") or ""),
                    source=str(application.get("application_channel") or job.get("source") or ""),
                    application_status=str(application["status"]),
                    created_at=cls._naive(application["created_at"]),
                    updated_at=cls._naive(application["updated_at"]),
                    salary_offered=cls._optional_float(job.get("salary_min")),
                    salary_ideal=cls._optional_float(job.get("salary_max")),
                    fit_score=None if score is None else float(score["total_score"]),
                    curriculum=curricula.get(application.get("curriculum_id"), ""),
                    cover_letter="" if letter_id is None else f"Carta #{letter_id}",
                    workflow_status="" if workflow is None else str(workflow["status"]),
                )
            )
        return result

    @classmethod
    def _drilldowns(
        cls,
        jobs: list[dict[str, object]],
        applications: list[dict[str, object]],
        executions: list[dict[str, object]],
        letters: list[dict[str, object]],
        rows: dict[str, list[dict[str, object]]],
        records: list[AnalyticsRecord],
        current: datetime,
    ) -> dict[str, tuple[DrilldownItem, ...]]:
        companies = {row["id"]: str(row["name"]) for row in rows.get("companies", [])}
        workflows = {row["id"]: str(row["name"]) for row in rows.get("workflows", [])}
        jobs_by_id = {row["id"]: row for row in rows.get("jobs", [])}
        job_items = tuple(
            DrilldownItem(
                "job", int(row["id"]), None,
                companies.get(row["company_id"], ""), str(row["title"]), str(row["status"]),
                cls._naive(row["created_at"]), str(row.get("source") or ""),
            )
            for row in jobs
        )
        record_items = tuple(cls._record_item(record) for record in records)
        execution_items = tuple(
            DrilldownItem(
                "workflow", int(row["id"]),
                None if row.get("application_id") is None else int(row["application_id"]),
                "", workflows.get(row["workflow_id"], ""), str(row["status"]),
                cls._naive(row["created_at"]), "",
            )
            for row in executions
        )
        letter_items = tuple(
            DrilldownItem(
                "cover_letter", int(row["id"]),
                None if row.get("application_id") is None else int(row["application_id"]),
                "", str(jobs_by_id.get(row.get("job_id"), {}).get("title") or ""), "Gerada",
                cls._naive(row["created_at"]), "",
            )
            for row in letters
        )
        return {
            "jobs_total": job_items,
            "jobs_active": tuple(
                item for item, row in zip(job_items, jobs, strict=True)
                if row["status"] not in cls.CLOSED_JOB_STATUSES
            ),
            "applications_total": record_items,
            "applications_in_progress": tuple(
                item for item, row in zip(record_items, applications, strict=True)
                if row["status"] not in cls.TERMINAL_APPLICATION_STATUSES
            ),
            "interviews": tuple(
                item for item, row in zip(record_items, applications, strict=True)
                if row["status"] in cls.INTERVIEW_STATUSES
            ),
            "offers": tuple(
                item for item, row in zip(record_items, applications, strict=True)
                if row["status"] in cls.OFFER_STATUSES
            ),
            "closed_or_rejected": tuple(
                item for item, row in zip(record_items, applications, strict=True)
                if row["status"] in {"Rejeitada", "Encerrada"}
            ),
            "workflows_awaiting_user": tuple(
                item for item, row in zip(execution_items, executions, strict=True)
                if row["status"] == "Aguardando usuário"
            ),
            "recent_failures": tuple(
                item for item, row in zip(execution_items, executions, strict=True)
                if row["status"] == "Falhou"
                and cls._naive(row["created_at"]) >= current - timedelta(days=cls.RECENT_FAILURE_DAYS)
            ),
            "cover_letters": letter_items,
            **{
                f"funnel:{status}": tuple(
                    item for item, row in zip(record_items, applications, strict=True)
                    if row["status"] == status
                )
                for status in ApplicationService.VALID_STATUS_TRANSITIONS
            },
        }

    @staticmethod
    def _record_item(record: AnalyticsRecord) -> DrilldownItem:
        return DrilldownItem(
            "application", record.application_id, record.job_id, record.company,
            record.title, record.application_status, record.updated_at, record.source,
        )

    @staticmethod
    def _optional_float(value: object) -> float | None:
        return None if value is None else float(value)

    @staticmethod
    def _rate(numerator: int, denominator: int) -> float:
        return round((numerator / denominator * 100) if denominator else 0.0, 2)

    @staticmethod
    def _parse_datetime(value: object) -> datetime:
        if isinstance(value, datetime):
            return AnalyticsService._naive(value)
        return AnalyticsService._naive(datetime.fromisoformat(str(value)))

    @staticmethod
    def _naive(value: object) -> datetime:
        if not isinstance(value, datetime):
            raise TypeError(f"Data inválida para analytics: {value!r}")
        if value.tzinfo is not None:
            return value.astimezone(UTC).replace(tzinfo=None)
        return value

    @staticmethod
    def _period_label(start: date | None, end: date | None) -> str:
        if start is None and end is None:
            return "Todo o período"
        return f"{start.isoformat() if start else 'início'} a {end.isoformat() if end else 'hoje'}"
