#!/usr/bin/env python3
"""Sprint 3.9 Architecture and Integration Guide

This document provides guidance for developers on the Sprint 3.9 architecture,
patterns, and how to use the platform services.
"""

# ============================================================================
# ARCHITECTURE OVERVIEW
# ============================================================================

"""
Sprint 3.9 follows Clean Architecture with 5 layers:

1. DOMAIN LAYER (acd/domain/platform/)
   - Pure business entities with no dependencies
   - Enums for state management
   - State verification methods
   - Serialization methods (to_dict)

2. INFRASTRUCTURE LAYER (acd/infrastructure/platform/)
   - Framework-specific implementations
   - External service integrations
   - Singleton service instances
   - Support for different operating systems

3. REPOSITORY LAYER (acd/infrastructure/repositories/platform/)
   - Data access abstraction
   - CRUD operations for all entities
   - Query filtering and sorting
   - Aggregation queries

4. APPLICATION LAYER (acd/application/platform/)
   - Business logic coordination
   - Service orchestration
   - Use case implementation
   - Cross-cutting concerns

5. PRESENTATION LAYER (acd/presentation/platform/)
   - UI components (PySide6)
   - User interaction handling
   - Display logic
   - Form validation
"""

# ============================================================================
# USING THE PLATFORM SERVICES
# ============================================================================


def example_health_monitoring():
    """Example: Using health monitoring in your code."""
    from sqlalchemy.orm import Session

    from acd.application.platform import PlatformUseCases

    session: Session = ...  # Your database session
    use_cases = PlatformUseCases(session)

    # Get current system health
    health = use_cases.get_system_health()
    print(f"System Status: {health['overall_status']}")

    # Run specific health check
    result = use_cases.run_health_check("DATABASE")
    if result.get("status") == "healthy":
        print("Database is healthy")


def example_configuration_management():
    """Example: Using centralized configuration."""

    # Set configuration
    use_cases.set_config("ai_service_timeout", 30, config_type="integer", category="ai")

    # Get configuration with type coercion
    timeout = use_cases.get_config("ai_service_timeout")  # Returns int 30

    # Get all settings in category
    ai_settings = use_cases.get_configuration_section("ai")


def example_backup_operations():
    """Example: Creating and restoring backups."""

    # Create backup
    backup_info = use_cases.create_backup(
        backup_dir="./backups", include_configs=True, include_logs=True
    )
    print(f"Backup created: {backup_info['name']}")

    # List available restore points
    restore_points = use_cases.list_restore_points()

    # Restore from backup
    result = use_cases.restore_from_backup(restore_points[0]["id"])


def example_metrics_collection():
    """Example: Collecting and analyzing metrics."""

    # Collect current metrics
    metrics = use_cases.collect_metrics()
    print(f"Memory: {metrics['memory_mb']:.1f}MB")
    print(f"CPU: {metrics['cpu_percent']:.1f}%")

    # Get metrics summary
    summary = use_cases.get_metrics_summary()

    # Get performance report
    report = use_cases.get_performance_report(hours=24)


def example_audit_logging():
    """Example: Using audit trail."""

    # Get audit trail
    audit = use_cases.get_audit_trail(module="application", days=7)

    # Get failed operations
    failures = use_cases.get_failed_operations(hours=24)

    # Generate compliance report
    report = use_cases.generate_compliance_report(days=30)


def example_structured_logging():
    """Example: Using structured logging."""
    from acd.infrastructure.platform import StructuredLogger

    logger = StructuredLogger("my_module")

    # Set correlation ID for request tracing
    logger.set_correlation_id("req-12345")

    # Simple logging
    logger.info("process_user", "User processing started")

    # Using context manager for automatic timing
    with logger.operation("database_query"):
        # Your database code here
        pass
    # Automatically logged with duration


# ============================================================================
# CREATING CUSTOM HEALTH CHECKS
# ============================================================================


def example_custom_health_check():
    """Example: Implementing a custom health check."""
    from acd.infrastructure.platform import (
        HealthCheck,
        get_registry,
    )

    class AIServiceHealthCheck(HealthCheck):
        """Custom health check for AI service."""

        def __init__(self, ai_service_url):
            self.url = ai_service_url

        def get_name(self) -> str:
            return "AI_SERVICE"

        def check(self) -> dict:
            import time

            import requests

            start_time = time.time()
            try:
                response = requests.get(f"{self.url}/health", timeout=5)
                duration_ms = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "message": "AI service responding normally",
                        "response_time_ms": duration_ms,
                    }
                else:
                    return {
                        "status": "degraded",
                        "message": f"AI service returned {response.status_code}",
                        "response_time_ms": duration_ms,
                    }
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                return {
                    "status": "unhealthy",
                    "message": f"AI service check failed: {str(e)}",
                    "error_message": str(e),
                    "response_time_ms": duration_ms,
                }

    # Register the check
    registry = get_registry()
    registry.register(AIServiceHealthCheck("http://localhost:8000"))


# ============================================================================
# DATABASE PATTERNS
# ============================================================================


def example_repository_usage():
    """Example: Using the repository pattern."""
    from acd.infrastructure.repositories.platform import PlatformRepository

    repository = PlatformRepository(session)

    # Create log entry
    log = repository.create_log(
        level="ERROR",
        module="authentication",
        operation="login",
        message="Failed login attempt",
        error_type="InvalidCredentials",
    )

    # Query logs
    recent_errors = repository.list_logs(
        level="ERROR", module="authentication", hours_back=24, limit=100
    )

    # Get metrics
    metrics = repository.get_metrics(
        metric_name="cpu_usage",
        hours_back=1,
    )

    # Backup operations
    backups = repository.list_backups(status="completed")


# ============================================================================
# CONFIGURATION PATTERNS
# ============================================================================


def example_configuration_setup():
    """Example: Setting up configuration sources."""
    from acd.infrastructure.platform import (
        ConfigurationProvider,
        DatabaseConfigurationSource,
        EnvironmentConfigurationSource,
        JsonFileConfigurationSource,
    )

    provider = ConfigurationProvider()

    # Add sources in priority order (first source wins)
    provider.add_source("database", DatabaseConfigurationSource(session))
    provider.add_source("json_file", JsonFileConfigurationSource("config.json"))
    provider.add_source("environment", EnvironmentConfigurationSource())

    # Configuration lookup cascades through sources
    timeout = provider.get("database_timeout")  # From database if exists, else JSON, else env


# ============================================================================
# TESTING PATTERNS
# ============================================================================


def example_test_setup():
    """Example: Setting up tests for platform services."""
    import pytest
    from sqlalchemy import create_engine

    from acd.application.platform import PlatformUseCases
    from acd.models.base import Base

    @pytest.fixture
    def temp_db():
        """Create in-memory test database."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        yield engine
        Base.metadata.drop_all(engine)

    @pytest.fixture
    def session(temp_db):
        """Create test session."""
        from sqlalchemy.orm import sessionmaker

        SessionLocal = sessionmaker(bind=temp_db)
        return SessionLocal()

    @pytest.fixture
    def use_cases(session):
        """Create use cases for testing."""
        return PlatformUseCases(session)

    def test_health_monitoring(use_cases):
        """Example test."""
        health = use_cases.get_system_health()
        assert health is not None


# ============================================================================
# ERROR HANDLING PATTERNS
# ============================================================================


def example_error_handling():
    """Example: Proper error handling in platform code."""
    from acd.infrastructure.platform import StructuredLogger

    logger = StructuredLogger("my_service")

    try:
        # Your operation here
        result = perform_operation()
    except ValueError as e:
        logger.error("perform_operation", f"Invalid value: {str(e)}", error_type="ValueError")
        raise
    except Exception as e:
        logger.critical(
            "perform_operation", f"Unexpected error: {str(e)}", error_type=type(e).__name__
        )
        raise


# ============================================================================
# MONITORING DASHBOARDS
# ============================================================================


def example_dashboard_data():
    """Example: Gathering data for monitoring dashboard."""

    def get_dashboard_data(use_cases) -> dict:
        """Gather all data for dashboard display."""
        return {
            # System health section
            "health": use_cases.get_system_health(),
            # Metrics section
            "metrics": use_cases.get_metrics_summary(),
            "performance": use_cases.get_performance_report(hours=24),
            # Backup section
            "backups": use_cases.list_backups(),
            "restore_points": use_cases.list_restore_points(),
            # Issues section
            "recent_errors": use_cases.get_failed_operations(hours=24),
            # Compliance section
            "compliance": use_cases.generate_compliance_report(days=30),
        }


# ============================================================================
# COMMON PATTERNS AND BEST PRACTICES
# ============================================================================

"""
1. SERVICE INITIALIZATION
   - Initialize services once during application startup
   - Use singleton pattern for shared infrastructure components
   - Inject dependencies explicitly

2. ERROR HANDLING
   - Always log errors with correlation IDs for tracing
   - Use structured logging with error_type and stack traces
   - Don't swallow exceptions, re-raise after logging

3. RESOURCE CLEANUP
   - Close database sessions after use
   - Clean up temporary files
   - Stop background tasks on shutdown

4. CONFIGURATION
   - Use centralized ConfigurationProvider
   - Don't hardcode values, make them configurable
   - Use environment variables for secrets

5. MONITORING
   - Record metrics at key operations
   - Use context managers for automatic timing
   - Set up health checks for critical systems

6. TESTING
   - Use in-memory SQLite for tests
   - Create separate test fixtures for each component
   - Test error paths as well as happy paths

7. LOGGING
   - Use correlation IDs for distributed tracing
   - Log at appropriate levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   - Include context metadata for debugging

8. PERFORMANCE
   - Index frequently queried fields
   - Use aggregation queries instead of fetching all data
   - Implement metric cleanup to prevent unbounded growth
"""


if __name__ == "__main__":
    # This is a documentation file, not executable
    print(__doc__)
