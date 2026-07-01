from __future__ import annotations

from typing import Optional

from sqlalchemy import select

from acd.database import database as database_module
from acd.domain.entities.metric import Metric
from acd.domain.entities.analytics_snapshot import AnalyticsSnapshot
from acd.domain.entities.report import Report
from acd.domain.entities.analytics_recommendation import AnalyticsRecommendation
from acd.domain.entities.trend import Trend


class AnalyticsRepository:
    """Repository for analytics data persistence."""

    def create_metric(self, metric_name: str, metric_value: float, *, dimension: str = "global", period: str = "daily") -> Metric:
        with database_module.SessionLocal() as session:
            metric = Metric(metric_name=metric_name, metric_value=metric_value, dimension=dimension, period=period)
            session.add(metric)
            session.commit()
            session.refresh(metric)
            return metric

    def get_metrics_by_name(self, metric_name: str) -> list[Metric]:
        with database_module.SessionLocal() as session:
            stmt = select(Metric).where(Metric.metric_name == metric_name).order_by(Metric.created_at.desc())
            return list(session.scalars(stmt).all())

    def create_snapshot(self, period: str, summary: str, kpis: str) -> AnalyticsSnapshot:
        with database_module.SessionLocal() as session:
            snapshot = AnalyticsSnapshot(period=period, summary=summary, kpis=kpis)
            session.add(snapshot)
            session.commit()
            session.refresh(snapshot)
            return snapshot

    def get_latest_snapshot(self) -> Optional[AnalyticsSnapshot]:
        with database_module.SessionLocal() as session:
            stmt = select(AnalyticsSnapshot).order_by(AnalyticsSnapshot.created_at.desc()).limit(1)
            return session.scalar(stmt)

    def create_report(self, title: str, period: str, content: str, *, format: str = "pdf") -> Report:
        with database_module.SessionLocal() as session:
            report = Report(title=title, period=period, content=content, format=format)
            session.add(report)
            session.commit()
            session.refresh(report)
            return report

    def list_reports(self) -> list[Report]:
        with database_module.SessionLocal() as session:
            return list(session.scalars(select(Report).order_by(Report.created_at.desc())).all())

    def create_recommendation(self, title: str, description: str, *, priority: str = "medium", action: str = "") -> AnalyticsRecommendation:
        with database_module.SessionLocal() as session:
            rec = AnalyticsRecommendation(title=title, description=description, priority=priority, action=action)
            session.add(rec)
            session.commit()
            session.refresh(rec)
            return rec

    def list_recommendations(self, unread_only: bool = False) -> list[AnalyticsRecommendation]:
        with database_module.SessionLocal() as session:
            if unread_only:
                stmt = select(AnalyticsRecommendation).where(AnalyticsRecommendation.read == False).order_by(AnalyticsRecommendation.created_at.desc())
            else:
                stmt = select(AnalyticsRecommendation).order_by(AnalyticsRecommendation.created_at.desc())
            return list(session.scalars(stmt).all())

    def create_trend(self, metric_name: str, value: float, period: str, *, dimension: str = "global") -> Trend:
        with database_module.SessionLocal() as session:
            trend = Trend(metric_name=metric_name, value=value, period=period, dimension=dimension)
            session.add(trend)
            session.commit()
            session.refresh(trend)
            return trend

    def get_trends(self, metric_name: str, dimension: str = "global") -> list[Trend]:
        with database_module.SessionLocal() as session:
            stmt = select(Trend).where((Trend.metric_name == metric_name) & (Trend.dimension == dimension)).order_by(Trend.created_at)
            return list(session.scalars(stmt).all())
