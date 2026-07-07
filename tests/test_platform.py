"""Test suite for Sprint 3.9 Platform Foundation."""

import os
import tempfile

import pytest
from sqlalchemy import create_engine

from acd.application.platform import PlatformUseCases
from acd.application.platform.services import (
    AuditService,
    BackupService,
    ConfigurationService,
    HealthService,
    MetricsService,
)
from acd.domain.platform import (
    BackupStatus,
    HealthCheckType,
    HealthStatus,
    LogLevel,
)
from acd.infrastructure.platform import (
    ConfigurationProvider,
    EnvironmentConfigurationSource,
    HealthCheckRegistry,
    JsonFileConfigurationSource,
    MemoryHealthCheck,
    MetricsCollector,
    StructuredLogger,
    get_registry,
)
from acd.infrastructure.repositories.platform import PlatformRepository
from acd.models.base import Base


@pytest.fixture
def temp_db():
    """Create temporary in-memory database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def session(temp_db):
    """Create database session."""
    Session = type("Session", (), {"__init__": lambda s: None})
    session = Session()
    session._connection = temp_db.connect()
    session._transaction = session._connection.begin()

    from sqlalchemy.orm import sessionmaker

    SessionLocal = sessionmaker(bind=temp_db)
    return SessionLocal()


@pytest.fixture
def repository(session):
    """Create repository."""
    return PlatformRepository(session)


@pytest.fixture
def use_cases(session):
    """Create use cases."""
    return PlatformUseCases(session)


# Infrastructure tests
class TestStructuredLogger:
    """Test StructuredLogger."""

    def test_logger_creation(self):
        """Test logger creation."""
        logger = StructuredLogger("test_module")
        assert logger.name == "test_module"

    def test_correlation_id_tracking(self):
        """Test correlation ID tracking."""
        logger = StructuredLogger("test")
        logger.set_correlation_id("test-correlation-123")
        context = logger.get_context()
        assert context["correlation_id"] == "test-correlation-123"

    def test_debug_logging(self):
        """Test debug logging."""
        logger = StructuredLogger("test")
        log_data = logger.debug("test_op", "test message")
        assert log_data["level"] == LogLevel.DEBUG.value
        assert log_data["message"] == "test message"

    def test_operation_context_manager(self):
        """Test operation context manager."""
        logger = StructuredLogger("test")
        with logger.operation("test_op"):
            pass
        # Should complete without error


class TestMetricsCollector:
    """Test MetricsCollector."""

    def test_collector_creation(self):
        """Test collector creation."""
        collector = MetricsCollector()
        assert collector is not None

    def test_system_metrics_collection(self):
        """Test system metrics collection."""
        collector = MetricsCollector()
        metrics = collector.collect_system_metrics()
        assert "memory_mb" in metrics
        assert "cpu_percent" in metrics
        assert "disk_usage_percent" in metrics

    def test_metric_recording(self):
        """Test metric recording."""
        collector = MetricsCollector()
        metric = collector.record_metric("test_metric", 42.0, "units")
        assert metric["metric_name"] == "test_metric"
        assert metric["metric_value"] == 42.0

    def test_metric_statistics(self):
        """Test metric statistics."""
        collector = MetricsCollector()
        collector.record_metric("test", 10.0)
        collector.record_metric("test", 20.0)
        collector.record_metric("test", 30.0)
        stats = collector.get_metric_statistics("test")
        assert stats is not None
        assert stats["min"] == 10.0
        assert stats["max"] == 30.0


class TestConfigurationProvider:
    """Test ConfigurationProvider."""

    def test_provider_creation(self):
        """Test provider creation."""
        provider = ConfigurationProvider()
        assert provider is not None

    def test_environment_source(self):
        """Test environment source."""
        source = EnvironmentConfigurationSource()
        source.set("test_key", "test_value")
        assert source.get("test_key") == "test_value"

    def test_json_file_source(self):
        """Test JSON file source."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{}")
            temp_file = f.name

        try:
            source = JsonFileConfigurationSource(temp_file)
            source.set("test_key", "test_value")
            assert source.get("test_key") == "test_value"
        finally:
            os.unlink(temp_file)

    def test_provider_cascading(self):
        """Test provider cascading through sources."""
        provider = ConfigurationProvider()
        provider.add_source("env", EnvironmentConfigurationSource())

        provider.set("test_key", "test_value", "env")
        assert provider.get("test_key") == "test_value"


class TestHealthCheckRegistry:
    """Test HealthCheckRegistry."""

    def test_registry_creation(self):
        """Test registry creation."""
        registry = HealthCheckRegistry()
        assert registry is not None

    def test_check_registration(self):
        """Test check registration."""
        registry = HealthCheckRegistry()
        check = MemoryHealthCheck()
        registry.register(check)
        assert HealthCheckType.MEMORY.value in registry.get_list()

    def test_run_all_checks(self):
        """Test running all checks."""
        registry = HealthCheckRegistry()
        registry.register(MemoryHealthCheck())
        results = registry.run_all()
        assert len(results) > 0

    def test_overall_status(self):
        """Test overall status calculation."""
        registry = HealthCheckRegistry()
        registry.register(MemoryHealthCheck())
        status = registry.get_overall_status()
        assert status in [s.value for s in HealthStatus]


# Repository tests
class TestPlatformRepository:
    """Test PlatformRepository."""

    def test_health_report_creation(self, repository):
        """Test health report creation."""
        report = repository.create_health_report(
            HealthCheckType.DATABASE.value, HealthStatus.HEALTHY.value, "All systems operational"
        )
        assert report.id is not None
        assert report.status == HealthStatus.HEALTHY.value

    def test_system_log_creation(self, repository):
        """Test system log creation."""
        log = repository.create_log(
            LogLevel.INFO.value, "test_module", "test_operation", "Test message"
        )
        assert log.id is not None
        assert log.module == "test_module"

    def test_metrics_recording(self, repository):
        """Test metrics recording."""
        metric = repository.record_metric("test_metric", 42.0, "units")
        assert metric.id is not None
        assert metric.metric_value == 42.0

    def test_backup_creation(self, repository):
        """Test backup creation."""
        from acd.domain.platform.backup import BackupType

        backup = repository.create_backup(BackupType.MANUAL.value, "test_backup", "/tmp/backup")
        assert backup.id is not None
        assert backup.name == "test_backup"

    def test_configuration_management(self, repository):
        """Test configuration management."""
        repository.set_config(
            "test_key",
            "test_value",
        )
        retrieved = repository.get_config("test_key")
        assert retrieved.value == "test_value"


# Service tests
class TestHealthService:
    """Test HealthService."""

    def test_health_service_creation(self, session):
        """Test health service creation."""
        service = HealthService(session)
        assert service is not None

    def test_run_health_checks(self, session):
        """Test running health checks."""
        service = HealthService(session)
        registry = get_registry()
        registry.register(MemoryHealthCheck())

        results = service.run_all_checks()
        assert len(results) > 0

    def test_get_health_history(self, session, repository):
        """Test getting health history."""
        repository.create_health_report(
            HealthCheckType.DATABASE.value, HealthStatus.HEALTHY.value, "Test"
        )
        service = HealthService(session)
        history = service.get_health_history()
        assert len(history) > 0


class TestBackupService:
    """Test BackupService."""

    def test_backup_service_creation(self, session):
        """Test backup service creation."""
        service = BackupService(session)
        assert service is not None

    def test_backup_listing(self, session, repository):
        """Test listing backups."""
        repository.create_backup(BackupStatus.COMPLETED.value, "test_backup", "/tmp/backup")
        service = BackupService(session)
        backups = service.list_backups()
        assert len(backups) > 0


class TestConfigurationService:
    """Test ConfigurationService."""

    def test_configuration_service_creation(self, session):
        """Test configuration service creation."""
        service = ConfigurationService(session)
        assert service is not None

    def test_get_and_set_config(self, session):
        """Test getting and setting config."""
        service = ConfigurationService(session)
        service.set_config("test_key", "test_value")
        value = service.get_config("test_key")
        assert value == "test_value"


class TestMetricsService:
    """Test MetricsService."""

    def test_metrics_service_creation(self, session):
        """Test metrics service creation."""
        service = MetricsService(session)
        assert service is not None

    def test_collect_system_metrics(self, session):
        """Test collecting system metrics."""
        service = MetricsService(session)
        metrics = service.collect_system_metrics()
        assert "memory_mb" in metrics
        assert "cpu_percent" in metrics


class TestAuditService:
    """Test AuditService."""

    def test_audit_service_creation(self, session):
        """Test audit service creation."""
        service = AuditService(session)
        assert service is not None

    def test_log_critical_operation(self, session):
        """Test logging critical operation."""
        service = AuditService(session)
        log = service.log_critical_operation("TEST_OPERATION", "test_module", user_id="test_user")
        assert log["operation"] == "TEST_OPERATION"

    def test_audit_trail(self, session, repository):
        """Test audit trail retrieval."""
        repository.create_log(
            LogLevel.WARNING.value, "test_module", "critical_op", "Critical operation"
        )
        service = AuditService(session)
        trail = service.get_audit_trail(module="test_module")
        assert len(trail) > 0


# Use cases tests
class TestPlatformUseCases:
    """Test PlatformUseCases orchestration."""

    def test_use_cases_creation(self, session):
        """Test use cases creation."""
        use_cases = PlatformUseCases(session)
        assert use_cases is not None

    def test_get_system_health(self, session):
        """Test getting system health."""
        use_cases = PlatformUseCases(session)
        registry = get_registry()
        registry.register(MemoryHealthCheck())

        health = use_cases.get_system_health()
        assert "overall_status" in health

    def test_collect_metrics(self, session):
        """Test collecting metrics."""
        use_cases = PlatformUseCases(session)
        metrics = use_cases.collect_metrics()
        assert "memory_mb" in metrics

    def test_get_configuration(self, session):
        """Test getting configuration."""
        use_cases = PlatformUseCases(session)
        use_cases.set_config("test_key", "test_value")
        value = use_cases.get_config("test_key")
        assert value == "test_value"

    def test_system_overview(self, session):
        """Test system overview."""
        use_cases = PlatformUseCases(session)
        registry = get_registry()
        registry.register(MemoryHealthCheck())

        overview = use_cases.get_system_overview()
        assert "health" in overview
        assert "metrics" in overview


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
