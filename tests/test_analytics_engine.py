import os
import tempfile

import pytest

from acd.database import database as database_module
from acd.infrastructure.repositories.analytics_repository import AnalyticsRepository
from acd.services.analytics_service import AnalyticsService
from acd.services.metrics_engine import MetricsEngine
from acd.services.recommendation_engine import RecommendationEngine
from acd.services.trend_analysis_service import TrendAnalysisService


@pytest.fixture
def temp_database(monkeypatch):
    """Create a temporary database for testing."""
    temp_dir = tempfile.mkdtemp(prefix="acd-analytics-", dir=".")
    db_path = os.path.join(temp_dir, "test_acd_analytics.db")
    monkeypatch.setattr(
        "acd.database.database.DATABASE_URL",
        f"sqlite:///{db_path}",
    )

    database_module.engine.dispose()
    database_module.engine = database_module.create_engine(
        f"sqlite:///{db_path}",
        echo=False,
        future=True,
    )
    database_module.SessionLocal = database_module.sessionmaker(
        bind=database_module.engine,
        autoflush=False,
        autocommit=False,
    )

    from acd.models.base import Base

    Base.metadata.drop_all(bind=database_module.engine)
    Base.metadata.create_all(bind=database_module.engine)

    yield

    Base.metadata.drop_all(bind=database_module.engine)


class TestMetricsEngine:
    """Test metrics calculation engine."""

    def test_calculate_conversion_metrics(self):
        """Test conversion metrics calculation."""
        engine = MetricsEngine()
        metrics = engine.calculate_conversion_metrics()

        assert metrics["jobs_found"] == 100
        assert metrics["applications"] == 45
        assert metrics["interviews"] == 8
        assert "conversion_application_rate" in metrics

    def test_calculate_ats_metrics(self):
        """Test ATS metrics calculation."""
        engine = MetricsEngine()
        metrics = engine.calculate_ats_metrics()

        assert metrics["average_ats"] == 72.5
        assert metrics["best_ats"] == 95
        assert "ats_trend" in metrics

    def test_calculate_platform_metrics(self):
        """Test platform metrics calculation."""
        engine = MetricsEngine()
        metrics = engine.calculate_platform_metrics()

        assert "platforms" in metrics
        assert "linkedin" in metrics["platforms"]
        assert "best_platform" in metrics

    def test_calculate_all_metrics(self):
        """Test complete metrics calculation."""
        engine = MetricsEngine()
        all_metrics = engine.calculate_all_metrics()

        assert "conversion" in all_metrics
        assert "ats" in all_metrics
        assert "curriculum" in all_metrics
        assert "platforms" in all_metrics
        assert "companies" in all_metrics
        assert "time" in all_metrics


class TestAnalyticsRepository:
    """Test analytics repository."""

    def test_create_metric(self, temp_database):
        """Test metric creation."""
        repo = AnalyticsRepository()
        metric = repo.create_metric("test_metric", 75.5)

        assert metric.metric_name == "test_metric"
        assert metric.metric_value == 75.5
        assert metric.id is not None

    def test_get_metrics_by_name(self, temp_database):
        """Test retrieving metrics by name."""
        repo = AnalyticsRepository()
        repo.create_metric("conversion_rate", 0.45)
        repo.create_metric("conversion_rate", 0.50)

        metrics = repo.get_metrics_by_name("conversion_rate")
        assert len(metrics) == 2

    def test_create_snapshot(self, temp_database):
        """Test snapshot creation."""
        repo = AnalyticsRepository()
        snapshot = repo.create_snapshot("daily", "Test summary", '{"kpi": 100}')

        assert snapshot.period == "daily"
        assert snapshot.summary == "Test summary"

    def test_create_recommendation(self, temp_database):
        """Test recommendation creation."""
        repo = AnalyticsRepository()
        rec = repo.create_recommendation(
            "Test Rec",
            "Test description",
            priority="high",
            action="test_action",
        )

        assert rec.title == "Test Rec"
        assert rec.priority == "high"

    def test_list_recommendations(self, temp_database):
        """Test listing recommendations."""
        repo = AnalyticsRepository()
        repo.create_recommendation("Rec1", "Desc1", priority="high")
        repo.create_recommendation("Rec2", "Desc2", priority="medium")

        recs = repo.list_recommendations()
        assert len(recs) == 2

    def test_create_and_get_trends(self, temp_database):
        """Test trend creation and retrieval."""
        repo = AnalyticsRepository()
        repo.create_trend("ats_average", 70.0, "daily")
        repo.create_trend("ats_average", 72.5, "daily")

        trends = repo.get_trends("ats_average")
        assert len(trends) == 2


class TestRecommendationEngine:
    """Test recommendation generation engine."""

    def test_generate_recommendations(self):
        """Test recommendation generation."""
        engine = RecommendationEngine()
        recs = engine.generate_recommendations()

        assert isinstance(recs, list)
        assert all("title" in rec for rec in recs)
        assert all("description" in rec for rec in recs)
        assert all("priority" in rec for rec in recs)


class TestTrendAnalysisService:
    """Test trend analysis service."""

    def test_analyze_ats_trend(self, temp_database):
        """Test ATS trend analysis."""
        service = TrendAnalysisService()
        trend = service.analyze_ats_trend()

        assert "trend" in trend
        assert "direction" in trend
        assert "data_points" in trend

    def test_analyze_conversion_trend(self, temp_database):
        """Test conversion trend analysis."""
        service = TrendAnalysisService()
        trend = service.analyze_conversion_trend()

        assert "trend" in trend
        assert "direction" in trend

    def test_get_all_trends(self, temp_database):
        """Test getting all trends."""
        service = TrendAnalysisService()
        trends = service.get_all_trends()

        assert "ats" in trends
        assert "conversion" in trends


class TestAnalyticsService:
    """Test main analytics service."""

    def test_calculate_kpis(self):
        """Test KPI calculation."""
        service = AnalyticsService()
        kpis = service.calculate_kpis()

        assert "conversion_to_interview" in kpis
        assert "average_ats" in kpis
        assert "total_applications" in kpis

    def test_generate_dashboard(self, temp_database):
        """Test complete dashboard generation."""
        service = AnalyticsService()
        dashboard = service.generate_dashboard()

        assert "kpis" in dashboard
        assert "metrics" in dashboard
        assert "trends" in dashboard
        assert "recommendations" in dashboard

    def test_get_conversion_funnel(self):
        """Test conversion funnel data."""
        service = AnalyticsService()
        funnel = service.get_conversion_funnel()

        assert len(funnel) == 5
        assert all("stage" in stage for stage in funnel)
        assert all("count" in stage for stage in funnel)

    def test_get_recommendations(self):
        """Test getting recommendations."""
        service = AnalyticsService()
        recs = service.get_recommendations()

        assert isinstance(recs, list)

    def test_create_snapshot(self, temp_database):
        """Test snapshot creation."""
        service = AnalyticsService()
        snapshot = service.create_snapshot("daily")

        assert "id" in snapshot
        assert "period" in snapshot
        assert snapshot["period"] == "daily"
