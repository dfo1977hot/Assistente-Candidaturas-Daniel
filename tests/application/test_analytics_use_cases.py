"""Behavioral tests for analytics application use cases."""

from __future__ import annotations

from types import SimpleNamespace

from acd.application.analytics.calculate_metrics import calculate_metrics
from acd.application.analytics.compare_results import compare_results
from acd.application.analytics.generate_dashboard import generate_dashboard
from acd.application.analytics.generate_recommendations import generate_recommendations


class AnalyticsServiceStub:
    """Records calls made by analytics application use cases."""

    def __init__(self) -> None:
        self.dashboard_calls = 0
        self.metrics_calls = 0

    def generate_dashboard(self) -> dict[str, int]:
        self.dashboard_calls += 1
        return {"applications": 3}

    def calculate_all_metrics(self) -> dict[str, float]:
        self.metrics_calls += 1
        return {"conversion": 0.5}


class RecommendationServiceStub:
    """Returns a deterministic recommendation set."""

    def generate_recommendations(self) -> list[dict[str, str]]:
        return [{"title": "Follow up", "priority": "high"}]


class AnalyticsRepositoryStub:
    """Provides the observable snapshot contract used by comparison."""

    def __init__(self, snapshot: object | None = None, *, raises: bool = False) -> None:
        self.snapshot = snapshot
        self.raises = raises

    def get_latest_snapshot(self) -> object | None:
        if self.raises:
            raise RuntimeError("database unavailable")
        return self.snapshot


def test_dashboard_and_metrics_delegate_to_injected_service() -> None:
    """Application use cases preserve the service results and call each operation once."""

    service = AnalyticsServiceStub()

    assert generate_dashboard(service) == {"applications": 3}
    assert calculate_metrics(service) == {"conversion": 0.5}
    assert service.dashboard_calls == 1
    assert service.metrics_calls == 1


def test_dashboard_and_metrics_create_default_service_when_not_supplied(monkeypatch) -> None:
    """Optional dependencies use the configured service constructors exactly once."""

    service = AnalyticsServiceStub()
    monkeypatch.setattr(
        "acd.application.analytics.generate_dashboard.AnalyticsService", lambda: service
    )
    monkeypatch.setattr(
        "acd.application.analytics.calculate_metrics.AnalyticsService", lambda: service
    )

    assert generate_dashboard() == {"applications": 3}
    assert calculate_metrics() == {"conversion": 0.5}
    assert service.dashboard_calls == 1
    assert service.metrics_calls == 1


def test_generate_recommendations_preserves_service_result() -> None:
    """Recommendations remain an application-level result without transformation."""

    result = generate_recommendations(RecommendationServiceStub())

    assert result == [{"title": "Follow up", "priority": "high"}]


def test_generate_recommendations_creates_default_service_when_not_supplied(monkeypatch) -> None:
    """The default recommendation dependency is used when no service is injected."""

    service = RecommendationServiceStub()
    monkeypatch.setattr(
        "acd.application.analytics.generate_recommendations.RecommendationEngine", lambda: service
    )

    assert generate_recommendations() == [{"title": "Follow up", "priority": "high"}]


def test_compare_results_reports_latest_snapshot_for_requested_periods() -> None:
    """Comparison reports the available snapshot and preserves requested periods."""

    snapshot = SimpleNamespace(id=7)

    result = compare_results(
        AnalyticsRepositoryStub(snapshot), period1="weekly", period2="monthly"
    )

    assert result == {
        "period1": "weekly",
        "period2": "monthly",
        "snapshots_found": 1,
        "comparison": {},
    }


def test_compare_results_tolerates_repository_failure() -> None:
    """A failed optional snapshot lookup still returns a valid empty comparison."""

    result = compare_results(AnalyticsRepositoryStub(raises=True))

    assert result["snapshots_found"] == 0
    assert result["comparison"] == {}


def test_compare_results_keeps_empty_history_when_no_snapshot_exists() -> None:
    """An empty repository history is distinct from a failed repository lookup."""

    result = compare_results(AnalyticsRepositoryStub())

    assert result["snapshots_found"] == 0
    assert result["comparison"] == {}
