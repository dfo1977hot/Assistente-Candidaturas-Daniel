"""Tests for MetricsEngine."""

from __future__ import annotations

from acd.services.metrics_engine import MetricsEngine


def test_metrics_engine_can_be_instantiated() -> None:
    """MetricsEngine should be instantiated."""

    engine = MetricsEngine()

    assert engine is not None


def test_calculate_conversion_metrics() -> None:
    """Should return conversion metrics."""

    engine = MetricsEngine()

    metrics = engine.calculate_conversion_metrics()

    assert metrics["jobs_found"] == 100
    assert metrics["applications"] == 45
    assert metrics["interviews"] == 8
    assert metrics["offers"] == 2
    assert metrics["hired"] == 1

    assert metrics["conversion_application_rate"] == 0.45
    assert metrics["conversion_interview_rate"] == 0.178
    assert metrics["conversion_offer_rate"] == 0.25
    assert metrics["conversion_final_rate"] == 0.01


def test_calculate_ats_metrics() -> None:
    """Should return ATS metrics."""

    engine = MetricsEngine()

    metrics = engine.calculate_ats_metrics()

    assert metrics["average_ats"] == 72.5
    assert metrics["best_ats"] == 95
    assert metrics["worst_ats"] == 35
    assert metrics["ats_trend"] == "up"
    assert metrics["applications_analyzed"] == 45


def test_calculate_curriculum_metrics() -> None:
    """Should return curriculum metrics."""

    engine = MetricsEngine()

    metrics = engine.calculate_curriculum_metrics()

    assert metrics["most_used_curriculum"] == "CV_v3"
    assert metrics["best_conversion_curriculum"] == "CV_v3"
    assert metrics["best_ats_curriculum"] == "CV_v2"
    assert metrics["total_curriculums"] == 5


def test_calculate_platform_metrics() -> None:
    """Should return platform metrics."""

    engine = MetricsEngine()

    metrics = engine.calculate_platform_metrics()

    assert metrics["best_platform"] == "workday"

    platforms = metrics["platforms"]

    assert "linkedin" in platforms
    assert "workday" in platforms
    assert "smartrecruiters" in platforms

    assert platforms["linkedin"]["applications"] == 25
    assert platforms["workday"]["applications"] == 12
    assert platforms["smartrecruiters"]["applications"] == 8


def test_calculate_company_metrics() -> None:
    """Should return company metrics."""

    engine = MetricsEngine()

    metrics = engine.calculate_company_metrics()

    assert "Google" in metrics["companies_with_most_interviews"]
    assert "Google" in metrics["companies_with_most_responses"]
    assert "Google" in metrics["companies_with_highest_approval_rate"]


def test_calculate_time_metrics() -> None:
    """Should return time metrics."""

    engine = MetricsEngine()

    metrics = engine.calculate_time_metrics()

    assert metrics["avg_time_to_response"] == 4.8
    assert metrics["avg_time_to_interview"] == 8.2
    assert metrics["avg_time_to_hiring"] == 32.5
    assert metrics["fastest_response"] == 1
    assert metrics["slowest_response"] == 45


def test_calculate_all_metrics() -> None:
    """Should aggregate every metrics group."""

    engine = MetricsEngine()

    metrics = engine.calculate_all_metrics()

    assert set(metrics.keys()) == {
        "conversion",
        "ats",
        "curriculum",
        "platforms",
        "companies",
        "time",
    }

    assert metrics["conversion"]["jobs_found"] == 100
    assert metrics["ats"]["average_ats"] == 72.5
    assert metrics["curriculum"]["most_used_curriculum"] == "CV_v3"
    assert metrics["platforms"]["best_platform"] == "workday"
    assert (
        metrics["companies"]["companies_with_most_interviews"][0]
        == "Google"
    )
    assert metrics["time"]["avg_time_to_response"] == 4.8