import pytest

from acd.infrastructure.repositories.analytics_repository import AnalyticsRepository
from acd.services.analytics_service import AnalyticsService
from acd.services.metrics_engine import MetricsEngine
from acd.services.recommendation_engine import RecommendationEngine
from acd.services.trend_analysis_service import TrendAnalysisService


@pytest.fixture
def temp_database(db_session):
    """Utiliza a infraestrutura compartilhada de banco."""
    yield db_session


class TestMetricsEngine:
    """Test metrics calculation engine."""

    def test_calculate_conversion_metrics(self):
        engine = MetricsEngine()
        metrics = engine.calculate_conversion_metrics()

        assert metrics["jobs_found"] == 100
        assert metrics["applications"] == 45
        assert metrics["interviews"] == 8
        assert "conversion_application_rate" in metrics

    def test_calculate_ats_metrics(self):
        engine = MetricsEngine()
        metrics = engine.calculate_ats_metrics()

        assert metrics["average_ats"] == 72.5
        assert metrics["best_ats"] == 95
        assert "ats_trend" in metrics

    def test_calculate_platform_metrics(self):
        engine = MetricsEngine()
        metrics = engine.calculate_platform_metrics()

        assert "platforms" in metrics
        assert "linkedin" in metrics["platforms"]
        assert "best_platform" in metrics

    def test_calculate_all_metrics(self):
        engine = MetricsEngine()
        all_metrics = engine.calculate_all_metrics()

        assert "conversion" in all_metrics
        assert "ats" in all_metrics
        assert "curriculum" in all_metrics
        assert "platforms" in all_metrics
        assert "companies" in all_metrics
        assert "time" in all_metrics


class TestAnalyticsRepository:

    def test_create_metric(self, temp_database):
        repo = AnalyticsRepository()
        metric = repo.create_metric("test_metric", 75.5)
        assert metric.metric_name == "test_metric"
        assert metric.metric_value == 75.5
        assert metric.id is not None

    def test_get_metrics_by_name(self, temp_database):
        repo = AnalyticsRepository()
        repo.create_metric("conversion_rate", 0.45)
        repo.create_metric("conversion_rate", 0.50)
        assert len(repo.get_metrics_by_name("conversion_rate")) == 2

    def test_create_snapshot(self, temp_database):
        repo = AnalyticsRepository()
        snapshot = repo.create_snapshot("daily", "Test summary", '{"kpi": 100}')
        assert snapshot.period == "daily"
        assert snapshot.summary == "Test summary"

    def test_create_recommendation(self, temp_database):
        repo = AnalyticsRepository()
        rec = repo.create_recommendation("Test Rec", "Test description", priority="high", action="test_action")
        assert rec.title == "Test Rec"
        assert rec.priority == "high"

    def test_list_recommendations(self, temp_database):
        repo = AnalyticsRepository()
        repo.create_recommendation("Rec1", "Desc1", priority="high")
        repo.create_recommendation("Rec2", "Desc2", priority="medium")
        assert len(repo.list_recommendations()) == 2

    def test_create_and_get_trends(self, temp_database):
        repo = AnalyticsRepository()
        repo.create_trend("ats_average", 70.0, "daily")
        repo.create_trend("ats_average", 72.5, "daily")
        assert len(repo.get_trends("ats_average")) == 2


class TestRecommendationEngine:

    def test_generate_recommendations(self):
        engine = RecommendationEngine()
        recs = engine.generate_recommendations()
        assert isinstance(recs, list)
        assert all("title" in r for r in recs)
        assert all("description" in r for r in recs)
        assert all("priority" in r for r in recs)


class TestTrendAnalysisService:

    def test_analyze_ats_trend(self, temp_database):
        trend = TrendAnalysisService().analyze_ats_trend()
        assert "trend" in trend
        assert "direction" in trend
        assert "data_points" in trend

    def test_analyze_conversion_trend(self, temp_database):
        trend = TrendAnalysisService().analyze_conversion_trend()
        assert "trend" in trend
        assert "direction" in trend

    def test_get_all_trends(self, temp_database):
        trends = TrendAnalysisService().get_all_trends()
        assert "ats" in trends
        assert "conversion" in trends


class TestAnalyticsService:

    def test_calculate_kpis(self):
        kpis = AnalyticsService().calculate_kpis()
        assert "conversion_to_interview" in kpis
        assert "average_ats" in kpis
        assert "total_applications" in kpis

    def test_generate_dashboard(self, temp_database):
        dashboard = AnalyticsService().generate_dashboard()
        assert "kpis" in dashboard
        assert "metrics" in dashboard
        assert "trends" in dashboard
        assert "recommendations" in dashboard

    def test_get_conversion_funnel(self):
        funnel = AnalyticsService().get_conversion_funnel()
        assert len(funnel) == 5
        assert all("stage" in s for s in funnel)
        assert all("count" in s for s in funnel)

    def test_get_recommendations(self):
        recs = AnalyticsService().get_recommendations()
        assert isinstance(recs, list)

    def test_create_snapshot(self, temp_database):
        snapshot = AnalyticsService().create_snapshot("daily")
        assert "id" in snapshot
        assert "period" in snapshot
        assert snapshot["period"] == "daily"
