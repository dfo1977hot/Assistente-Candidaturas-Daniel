"""Tests for TrendAnalysisService."""

from __future__ import annotations

from types import SimpleNamespace

from acd.services.trend_analysis_service import TrendAnalysisService


class FakeRepository:
    """Fake analytics repository."""

    def __init__(self) -> None:
        self.created: list[tuple] = []
        self._trends: dict[str, list[SimpleNamespace]] = {}

    def get_trends(self, metric_name: str, dimension: str = "global"):
        return self._trends.get(metric_name, [])

    def create_trend(
        self,
        metric_name: str,
        value: float,
        period: str,
        *,
        dimension: str = "global",
    ) -> None:
        self.created.append(
            (metric_name, value, period, dimension)
        )


def create_service(repository: FakeRepository) -> TrendAnalysisService:
    """Create service with fake repository."""

    return TrendAnalysisService(repository=repository)


def test_analyze_ats_trend_without_data() -> None:
    """Should return neutral trend when there is no data."""

    repository = FakeRepository()
    service = create_service(repository)

    result = service.analyze_ats_trend()

    assert result == {
        "trend": "stable",
        "direction": "neutral",
        "data_points": 0,
    }


def test_analyze_ats_trend_up() -> None:
    """Should detect upward trend."""

    repository = FakeRepository()

    repository._trends["ats_average"] = [
        SimpleNamespace(value=v)
        for v in [60, 62, 63, 70, 74, 78]
    ]

    service = create_service(repository)

    result = service.analyze_ats_trend()

    assert result["trend"] == "up"
    assert result["direction"] == "up"
    assert result["data_points"] == 6
    assert result["current_value"] == 78


def test_analyze_ats_trend_down() -> None:
    """Should detect downward trend."""

    repository = FakeRepository()

    repository._trends["ats_average"] = [
        SimpleNamespace(value=v)
        for v in [80, 78, 75, 70, 66, 60]
    ]

    service = create_service(repository)

    result = service.analyze_ats_trend()

    assert result["trend"] == "down"
    assert result["direction"] == "down"


def test_analyze_conversion_trend_without_data() -> None:
    """Should return neutral trend."""

    repository = FakeRepository()
    service = create_service(repository)

    result = service.analyze_conversion_trend()

    assert result == {
        "trend": "stable",
        "direction": "neutral",
        "data_points": 0,
    }


def test_analyze_conversion_trend_up() -> None:
    """Should detect upward conversion trend."""

    repository = FakeRepository()

    repository._trends["conversion_rate"] = [
        SimpleNamespace(value=v)
        for v in [0.12, 0.18]
    ]

    service = create_service(repository)

    result = service.analyze_conversion_trend()

    assert result["trend"] == "up"
    assert result["direction"] == "up"
    assert result["current_value"] == 0.18


def test_record_metric_trend() -> None:
    """Should delegate trend persistence."""

    repository = FakeRepository()

    service = create_service(repository)

    service.record_metric_trend(
        metric_name="ats_average",
        value=80.5,
        period="daily",
    )

    assert repository.created == [
        (
            "ats_average",
            80.5,
            "daily",
            "global",
        )
    ]


def test_get_all_trends() -> None:
    """Should aggregate all trend analyses."""

    repository = FakeRepository()

    repository._trends["ats_average"] = [
        SimpleNamespace(value=v)
        for v in [60, 65, 70]
    ]

    repository._trends["conversion_rate"] = [
        SimpleNamespace(value=v)
        for v in [0.10, 0.15]
    ]

    service = create_service(repository)

    trends = service.get_all_trends()

    assert set(trends.keys()) == {
        "ats",
        "conversion",
    }

    assert trends["ats"]["trend"] == "up"
    assert trends["conversion"]["trend"] == "up"