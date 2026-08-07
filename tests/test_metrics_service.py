from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from acd.application.platform.services.metrics_service import (
    MetricsService,
)


@pytest.fixture
def metrics_service(monkeypatch):
    """
    Creates MetricsService with mocked dependencies.
    """

    session = MagicMock()

    repository = MagicMock()

    collector = MagicMock()

    logger = MagicMock()

    operation = MagicMock()
    operation.__enter__.return_value = None
    operation.__exit__.return_value = None

    logger.operation.return_value = operation

    monkeypatch.setattr(
        "acd.application.platform.services.metrics_service.PlatformRepository",
        lambda session: repository,
    )

    monkeypatch.setattr(
        "acd.application.platform.services.metrics_service.StructuredLogger",
        lambda name: logger,
    )

    monkeypatch.setattr(
        "acd.application.platform.services.metrics_service.get_collector",
        lambda: collector,
    )

    service = MetricsService(session)

    return (
        service,
        repository,
        collector,
        logger,
    )


def create_metric(
    *,
    metric_name="cpu_usage",
    metric_value=10.5,
    unit="%",
    module="system",
    category="resource",
    status="ok",
):
    return SimpleNamespace(
        metric_name=metric_name,
        metric_value=metric_value,
        unit=unit,
        module=module,
        category=category,
        status=status,
        timestamp=datetime(2026, 1, 1, 12, 0, 0),
    )


def test_collect_system_metrics(metrics_service):
    service, repository, collector, _ = metrics_service

    collector.collect_system_metrics.return_value = {
        "memory_mb": 512,
        "cpu_percent": 30,
        "disk_usage_percent": 40,
        "uptime_seconds": 1000,
    }

    result = service.collect_system_metrics()

    assert result["memory_mb"] == 512
    assert result["cpu_percent"] == 30

    assert repository.record_metric.call_count == 3


def test_record_metric(metrics_service):
    service, repository, _, _ = metrics_service

    repository.record_metric.return_value = create_metric(
        metric_name="temperature",
        metric_value=55,
        unit="C",
    )

    result = service.record_metric(
        "temperature",
        55,
        unit="C",
    )

    assert result["metric_name"] == "temperature"
    assert result["value"] == 55
    assert result["unit"] == "C"

    repository.record_metric.assert_called_once()


def test_record_metric_without_timestamp(metrics_service):
    service, repository, _, _ = metrics_service

    metric = create_metric()
    metric.timestamp = None

    repository.record_metric.return_value = metric

    result = service.record_metric(
        "cpu",
        10,
    )

    assert result["timestamp"] is None


def test_get_metrics(metrics_service):
    service, repository, _, _ = metrics_service

    repository.get_metrics.return_value = [
        create_metric(
            metric_name="cpu_usage",
            metric_value=20,
        ),
        create_metric(
            metric_name="memory_usage",
            metric_value=500,
            unit="MB",
        ),
    ]

    result = service.get_metrics()

    assert len(result) == 2

    repository.get_metrics.assert_called_once_with(
        metric_name=None,
        category=None,
        hours_back=1,
    )


def test_get_metrics_without_timestamp(metrics_service):
    service, repository, _, _ = metrics_service

    metric = create_metric()
    metric.timestamp = None

    repository.get_metrics.return_value = [metric]

    result = service.get_metrics()

    assert result[0]["timestamp"] is None


def test_get_metric_statistics(metrics_service):
    service, _, collector, _ = metrics_service

    collector.get_metric_statistics.return_value = {
        "avg": 25,
        "max": 30,
    }

    result = service.get_metric_statistics(
        "cpu_usage",
        120,
    )

    assert result["avg"] == 25

    collector.get_metric_statistics.assert_called_once_with(
        "cpu_usage",
        120,
    )


def test_get_system_summary(metrics_service):
    service, _, _, _ = metrics_service

    service.collect_system_metrics = MagicMock(
        return_value={
            "memory_mb": 1024,
            "cpu_percent": 25,
            "disk_usage_percent": 60,
            "uptime_seconds": 3600,
        }
    )

    service.get_metric_statistics = MagicMock(
        side_effect=[
            {"avg": 900, "max": 1200},
            {"avg": 20, "max": 35},
            {"avg": 55, "max": 75},
        ]
    )

    summary = service.get_system_summary()

    assert summary["current"]["memory_mb"] == 1024
    assert summary["current"]["cpu_percent"] == 25
    assert summary["current"]["disk_usage_percent"] == 60
    assert summary["current"]["uptime_seconds"] == 3600

    assert summary["averages"]["memory_mb"] == 900
    assert summary["averages"]["cpu_percent"] == 20
    assert summary["averages"]["disk_usage_percent"] == 55

    assert summary["extremes"]["memory_max"] == 1200
    assert summary["extremes"]["cpu_max"] == 35
    assert summary["extremes"]["disk_max"] == 75

    assert "timestamp" in summary


def test_get_system_summary_without_statistics(metrics_service):
    service, _, _, _ = metrics_service

    service.collect_system_metrics = MagicMock(
        return_value={
            "memory_mb": 256,
            "cpu_percent": 5,
            "disk_usage_percent": 10,
            "uptime_seconds": 100,
        }
    )

    service.get_metric_statistics = MagicMock(
        return_value=None,
    )

    summary = service.get_system_summary()

    assert summary["averages"]["memory_mb"] is None
    assert summary["averages"]["cpu_percent"] is None
    assert summary["averages"]["disk_usage_percent"] is None

    assert summary["extremes"]["memory_max"] is None
    assert summary["extremes"]["cpu_max"] is None
    assert summary["extremes"]["disk_max"] is None


def test_get_system_summary_partial_statistics(metrics_service):
    service, _, _, _ = metrics_service

    service.collect_system_metrics = MagicMock(
        return_value={
            "memory_mb": 500,
            "cpu_percent": 40,
            "disk_usage_percent": 50,
            "uptime_seconds": 900,
        }
    )

    service.get_metric_statistics = MagicMock(
        side_effect=[
            {"avg": 480, "max": 600},
            None,
            {"avg": 49, "max": 55},
        ]
    )

    summary = service.get_system_summary()

    assert summary["averages"]["memory_mb"] == 480
    assert summary["averages"]["cpu_percent"] is None
    assert summary["averages"]["disk_usage_percent"] == 49

    assert summary["extremes"]["memory_max"] == 600
    assert summary["extremes"]["cpu_max"] is None
    assert summary["extremes"]["disk_max"] == 55


def test_get_metrics_with_filters(metrics_service):
    service, repository, _, _ = metrics_service

    repository.get_metrics.return_value = []

    service.get_metrics(
        metric_name="cpu_usage",
        category="resource",
        hours_back=12,
    )

    repository.get_metrics.assert_called_once_with(
        metric_name="cpu_usage",
        category="resource",
        hours_back=12,
    )


def test_get_performance_report(metrics_service):
    service, _, _, _ = metrics_service

    service.get_metrics = MagicMock(
        side_effect=[
            [
                {"value": 100},
                {"value": 200},
                {"value": 300},
            ],
            [
                {"value": 10},
                {"value": 20},
                {"value": 30},
            ],
        ]
    )

    report = service.get_performance_report(24)

    assert report["period_hours"] == 24

    assert report["memory"]["min"] == 100
    assert report["memory"]["max"] == 300
    assert report["memory"]["avg"] == 200
    assert report["memory"]["count"] == 3

    assert report["cpu"]["min"] == 10
    assert report["cpu"]["max"] == 30
    assert report["cpu"]["avg"] == 20
    assert report["cpu"]["count"] == 3

    assert "report_timestamp" in report


def test_get_performance_report_without_metrics(metrics_service):
    service, _, _, _ = metrics_service

    service.get_metrics = MagicMock(
        side_effect=[
            [],
            [],
        ]
    )

    report = service.get_performance_report()

    assert report["memory"] is None
    assert report["cpu"] is None


def test_get_performance_report_only_memory(metrics_service):
    service, _, _, _ = metrics_service

    service.get_metrics = MagicMock(
        side_effect=[
            [
                {"value": 512},
            ],
            [],
        ]
    )

    report = service.get_performance_report()

    assert report["memory"]["count"] == 1
    assert report["memory"]["avg"] == 512

    assert report["cpu"] is None


def test_get_performance_report_only_cpu(metrics_service):
    service, _, _, _ = metrics_service

    service.get_metrics = MagicMock(
        side_effect=[
            [],
            [
                {"value": 35},
                {"value": 45},
            ],
        ]
    )

    report = service.get_performance_report()

    assert report["memory"] is None

    assert report["cpu"]["count"] == 2
    assert report["cpu"]["min"] == 35
    assert report["cpu"]["max"] == 45
    assert report["cpu"]["avg"] == 40


def test_cleanup_old_metrics(metrics_service):
    service, _, collector, _ = metrics_service

    collector.clear_old_metrics.return_value = 17

    result = service.cleanup_old_metrics(48)

    assert result == 17

    collector.clear_old_metrics.assert_called_once_with(
        48,
    )


def test_cleanup_old_metrics_default_value(metrics_service):
    service, _, collector, _ = metrics_service

    collector.clear_old_metrics.return_value = 5

    result = service.cleanup_old_metrics()

    assert result == 5

    collector.clear_old_metrics.assert_called_once_with(
        24,
    )


def test_record_metric_with_tags(metrics_service):
    service, repository, _, _ = metrics_service

    repository.record_metric.return_value = create_metric(
        metric_name="temperature",
        metric_value=42,
        unit="C",
    )

    service.record_metric(
        "temperature",
        42,
        unit="C",
        tags=["prod", "node1"],
    )

    repository.record_metric.assert_called_once_with(
        "temperature",
        42,
        unit="C",
        module="system",
        category="performance",
        tags=["prod", "node1"],
    )


def test_record_metric_without_tags(metrics_service):
    service, repository, _, _ = metrics_service

    repository.record_metric.return_value = create_metric()

    service.record_metric(
        "cpu_usage",
        15,
    )

    repository.record_metric.assert_called_once_with(
        "cpu_usage",
        15,
        unit="",
        module="system",
        category="performance",
        tags=[],
    )