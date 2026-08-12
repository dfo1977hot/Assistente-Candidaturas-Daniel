from __future__ import annotations

from sqlalchemy import select

from acd.database import database as database_module
from acd.domain.entities.analytics_recommendation import (
    AnalyticsRecommendation,
)
from acd.domain.entities.analytics_snapshot import (
    AnalyticsSnapshot,
)
from acd.domain.entities.application import Application
from acd.domain.entities.ats_score import ATSScore
from acd.domain.entities.cover_letter_version import CoverLetterVersion
from acd.domain.entities.curriculum import Curriculum
from acd.domain.entities.job import Job
from acd.domain.entities.metric import Metric
from acd.domain.entities.report import Report
from acd.domain.entities.resume_version import ResumeVersion
from acd.domain.entities.trend import Trend
from acd.domain.entities.workflow import Workflow
from acd.domain.entities.workflow_execution import WorkflowExecution
from acd.models.company import Company


class AnalyticsRepository:
    """Repository for analytics data persistence."""

    def load_operational_data(self) -> dict[str, list[dict[str, object]]]:
        """Load compact real-data projections used by the operational dashboard."""
        with database_module.SessionLocal() as session:
            queries = {
                "companies": select(Company.id, Company.name),
                "jobs": select(
                    Job.id,
                    Job.company_id,
                    Job.title,
                    Job.status,
                    Job.source,
                    Job.salary_min,
                    Job.salary_max,
                    Job.created_at,
                    Job.updated_at,
                ),
                "applications": select(
                    Application.id,
                    Application.job_id,
                    Application.company_id,
                    Application.status,
                    Application.application_channel,
                    Application.created_at,
                    Application.updated_at,
                    Application.last_update,
                    Application.next_follow_up,
                    Application.interview_date,
                    Application.next_action,
                    Application.follow_up_priority,
                    Application.curriculum_id,
                    Application.cover_letter_id,
                ),
                "workflows": select(
                    Workflow.id,
                    Workflow.name,
                    Workflow.active,
                    Workflow.definition,
                ),
                "workflow_executions": select(
                    WorkflowExecution.id,
                    WorkflowExecution.workflow_id,
                    WorkflowExecution.application_id,
                    WorkflowExecution.status,
                    WorkflowExecution.started_at,
                    WorkflowExecution.finished_at,
                    WorkflowExecution.created_at,
                    WorkflowExecution.result,
                ),
                "cover_letters": select(
                    CoverLetterVersion.id,
                    CoverLetterVersion.job_id,
                    CoverLetterVersion.application_id,
                    CoverLetterVersion.created_at,
                ),
                "resume_versions": select(
                    ResumeVersion.id,
                    ResumeVersion.created_at,
                ),
                "curricula": select(Curriculum.id, Curriculum.name),
                "ats_scores": select(
                    ATSScore.id,
                    ATSScore.application_id,
                    ATSScore.total_score,
                    ATSScore.calculated_at,
                ),
            }
            return {
                name: [dict(row) for row in session.execute(query).mappings().all()]
                for name, query in queries.items()
            }

    def create_metric(
        self,
        metric_name: str,
        metric_value: float,
        *,
        dimension: str = "global",
        period: str = "daily",
    ) -> Metric:
        with database_module.SessionLocal() as session:
            metric = Metric(
                metric_name=metric_name,
                metric_value=metric_value,
                dimension=dimension,
                period=period,
            )
            session.add(metric)
            session.commit()
            session.refresh(metric)
            return metric

    def get_metrics_by_name(
        self,
        metric_name: str,
    ) -> list[Metric]:
        with database_module.SessionLocal() as session:
            stmt = (
                select(Metric)
                .where(Metric.metric_name == metric_name)
                .order_by(Metric.created_at.desc())
            )

            return list(session.scalars(stmt).all())

    def create_snapshot(
        self,
        period: str,
        summary: str,
        kpis: str,
    ) -> AnalyticsSnapshot:
        with database_module.SessionLocal() as session:
            snapshot = AnalyticsSnapshot(
                period=period,
                summary=summary,
                kpis=kpis,
            )

            session.add(snapshot)
            session.commit()
            session.refresh(snapshot)

            return snapshot

    def get_latest_snapshot(
        self,
    ) -> AnalyticsSnapshot | None:
        with database_module.SessionLocal() as session:
            stmt = (
                select(AnalyticsSnapshot)
                .order_by(
                    AnalyticsSnapshot.created_at.desc(),
                )
                .limit(1)
            )

            return session.scalar(stmt)

    def create_report(
        self,
        title: str,
        period: str,
        content: str,
        *,
        format: str = "pdf",
    ) -> Report:
        with database_module.SessionLocal() as session:
            report = Report(
                title=title,
                period=period,
                content=content,
                format=format,
            )

            session.add(report)
            session.commit()
            session.refresh(report)

            return report

    def list_reports(self) -> list[Report]:
        with database_module.SessionLocal() as session:
            stmt = (
                select(Report)
                .order_by(
                    Report.created_at.desc(),
                )
            )

            return list(session.scalars(stmt).all())

    def create_recommendation(
        self,
        title: str,
        description: str,
        *,
        priority: str = "medium",
        action: str = "",
    ) -> AnalyticsRecommendation:
        with database_module.SessionLocal() as session:
            recommendation = AnalyticsRecommendation(
                title=title,
                description=description,
                priority=priority,
                action=action,
            )

            session.add(recommendation)
            session.commit()
            session.refresh(recommendation)

            return recommendation

    def list_recommendations(
        self,
        unread_only: bool = False,
    ) -> list[AnalyticsRecommendation]:
        with database_module.SessionLocal() as session:

            if unread_only:
                stmt = (
                    select(AnalyticsRecommendation)
                    .where(
                        AnalyticsRecommendation.read.is_(False),
                    )
                    .order_by(
                        AnalyticsRecommendation.created_at.desc(),
                    )
                )
            else:
                stmt = (
                    select(AnalyticsRecommendation)
                    .order_by(
                        AnalyticsRecommendation.created_at.desc(),
                    )
                )

            return list(session.scalars(stmt).all())

    def create_trend(
        self,
        metric_name: str,
        value: float,
        period: str,
        *,
        dimension: str = "global",
    ) -> Trend:
        with database_module.SessionLocal() as session:
            trend = Trend(
                metric_name=metric_name,
                value=value,
                period=period,
                dimension=dimension,
            )

            session.add(trend)
            session.commit()
            session.refresh(trend)

            return trend

    def get_trends(
        self,
        metric_name: str,
        dimension: str = "global",
    ) -> list[Trend]:
        with database_module.SessionLocal() as session:
            stmt = (
                select(Trend)
                .where(
                    (Trend.metric_name == metric_name)
                    & (Trend.dimension == dimension)
                )
                .order_by(
                    Trend.created_at,
                )
            )

            return list(session.scalars(stmt).all())
