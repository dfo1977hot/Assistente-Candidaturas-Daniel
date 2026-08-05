from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from acd.application.release.services.migration_service import (
    DocumentationService,
    MigrationService,
)


@pytest.fixture
def migration_service(monkeypatch):
    """Create MigrationService with mocked dependencies."""

    session = MagicMock()

    repository = MagicMock()

    logger = MagicMock()

    operation = MagicMock()
    operation.__enter__.return_value = None
    operation.__exit__.return_value = None

    logger.operation.return_value = operation

    monkeypatch.setattr(
        "acd.application.release.services.migration_service.ReleaseRepository",
        lambda session: repository,
    )

    monkeypatch.setattr(
        "acd.application.release.services.migration_service.StructuredLogger",
        lambda name: logger,
    )

    service = MigrationService(session)

    return (
        service,
        session,
        repository,
        logger,
    )


def make_migration(
    migration_id: int = 10,
):
    """Create fake migration entity."""

    migration = MagicMock()

    migration.id = migration_id

    migration.to_dict.return_value = {
        "id": migration_id,
    }

    return migration


def test_service_creation(
    migration_service,
):
    """Service initialization."""

    service, session, repository, logger = migration_service

    assert service.session is session
    assert service.repository is repository
    assert service.logger is logger


def test_create_migration_success(
    migration_service,
):
    """Successful migration."""

    service, _, repository, _ = migration_service

    repository.create_migration_history.return_value = (
        make_migration()
    )

    result = service.create_migration(
        "1.0.0",
        "2.0.0",
    )

    assert result == {
        "success": True,
        "migration_id": 10,
        "message": "Migration completed: 1.0.0 → 2.0.0",
    }

    repository.create_migration_history.assert_called_once_with(
        migration_name="v1.0.0_to_v2.0.0_database",
        source_version="1.0.0",
        target_version="2.0.0",
        migration_type="database",
    )

    repository.update_migration_status.assert_called_once_with(
        10,
        status="completed",
        records_migrated=0,
        records_failed=0,
        duration_seconds=1,
    )


def test_create_migration_custom_type(
    migration_service,
):
    """Migration with custom type."""

    service, _, repository, _ = migration_service

    repository.create_migration_history.return_value = (
        make_migration(
            20,
        )
    )

    result = service.create_migration(
        "1.0.0",
        "2.0.0",
        migration_type="configuration",
    )

    assert result["success"] is True
    assert result["migration_id"] == 20

    repository.create_migration_history.assert_called_once_with(
        migration_name="v1.0.0_to_v2.0.0_configuration",
        source_version="1.0.0",
        target_version="2.0.0",
        migration_type="configuration",
    )


def test_create_migration_invalid_version(
    migration_service,
):
    """Invalid semantic version."""

    service, _, _, logger = migration_service

    result = service.create_migration(
        "invalid",
        "2.0.0",
    )

    assert result["success"] is False
    assert result["migration_id"] is None

    assert "Invalid semantic version format" in result["message"]

    logger.error.assert_called_once()


def test_create_migration_repository_exception(
    migration_service,
):
    """Repository exception."""

    service, _, repository, logger = migration_service

    repository.create_migration_history.side_effect = RuntimeError(
        "database failure",
    )

    result = service.create_migration(
        "1.0.0",
        "2.0.0",
    )

    assert result["success"] is False
    assert result["migration_id"] is None

    assert "database failure" in result["message"]

    logger.error.assert_called_once()


def test_get_migration_history_empty(
    migration_service,
):
    """No migration history."""

    service, _, repository, _ = migration_service

    repository.list_migration_history.return_value = []

    result = service.get_migration_history()

    assert result == []

    repository.list_migration_history.assert_called_once_with(
        limit=50,
    )


def test_get_migration_history(
    migration_service,
):
    """Migration history."""

    service, _, repository, _ = migration_service

    migration1 = make_migration(1)
    migration2 = make_migration(2)

    repository.list_migration_history.return_value = [
        migration1,
        migration2,
    ]

    result = service.get_migration_history(
        limit=5,
    )

    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[1]["id"] == 2

    repository.list_migration_history.assert_called_once_with(
        limit=5,
    )


def test_validate_migration_compatible(
    migration_service,
):
    """Migration should be compatible."""

    service, *_ = migration_service

    result = service.validate_migration_compatibility(
        "1.0.0",
        "2.0.0",
    )

    assert result == {
        "is_compatible": True,
        "message": "Migration path: 1.0.0 → 2.0.0",
    }


def test_validate_migration_same_version(
    migration_service,
):
    """Cannot migrate to same version."""

    service, *_ = migration_service

    result = service.validate_migration_compatibility(
        "1.0.0",
        "1.0.0",
    )

    assert result == {
        "is_compatible": False,
        "message": "Cannot migrate to same or older version",
    }


def test_validate_migration_older_version(
    migration_service,
):
    """Cannot migrate backwards."""

    service, *_ = migration_service

    result = service.validate_migration_compatibility(
        "2.0.0",
        "1.0.0",
    )

    assert result == {
        "is_compatible": False,
        "message": "Cannot migrate to same or older version",
    }


def test_validate_migration_large_gap(
    migration_service,
):
    """Major version gap too large."""

    service, *_ = migration_service

    result = service.validate_migration_compatibility(
        "1.0.0",
        "4.0.0",
    )

    assert result == {
        "is_compatible": False,
        "message": "Version gap too large (3 major versions)",
    }


def test_validate_migration_invalid_source_version(
    migration_service,
):
    """Invalid source version."""

    service, *_ = migration_service

    result = service.validate_migration_compatibility(
        "invalid",
        "2.0.0",
    )

    assert result["is_compatible"] is False
    assert "Invalid semantic version format" in result["message"]


def test_validate_migration_invalid_target_version(
    migration_service,
):
    """Invalid target version."""

    service, *_ = migration_service

    result = service.validate_migration_compatibility(
        "1.0.0",
        "invalid",
    )

    assert result["is_compatible"] is False
    assert "Invalid semantic version format" in result["message"]


@pytest.fixture
def documentation_service(monkeypatch):
    """Create DocumentationService with mocked dependencies."""

    session = MagicMock()

    repository = MagicMock()

    logger = MagicMock()

    monkeypatch.setattr(
        "acd.application.release.services.migration_service.ReleaseRepository",
        lambda session: repository,
    )

    monkeypatch.setattr(
        "acd.application.release.services.migration_service.StructuredLogger",
        lambda name: logger,
    )

    service = DocumentationService(session)

    return (
        service,
        session,
        repository,
        logger,
    )


def make_topic(
    topic_id: str = "intro",
):
    """Create fake documentation topic."""

    topic = MagicMock()

    topic.id = 1
    topic.topic_id = topic_id
    topic.title = "Introduction"
    topic.category = "general"
    topic.content = "Documentation"
    topic.view_count = 5

    topic.to_dict.return_value = {
        "id": topic.id,
        "topic_id": topic.topic_id,
        "title": topic.title,
    }

    return topic


def test_documentation_service_creation(
    documentation_service,
):
    """DocumentationService initialization."""

    service, session, repository, logger = documentation_service

    assert service.session is session
    assert service.repository is repository
    assert service.logger is logger


def test_search_documentation_empty(
    documentation_service,
):
    """No documentation found."""

    service, _, repository, _ = documentation_service

    repository.search_documentation.return_value = []

    result = service.search_documentation(
        "install",
    )

    assert result == []

    repository.search_documentation.assert_called_once_with(
        "install",
        limit=20,
    )


def test_search_documentation(
    documentation_service,
):
    """Search documentation."""

    service, _, repository, _ = documentation_service

    topic1 = make_topic("install")
    topic2 = make_topic("upgrade")

    repository.search_documentation.return_value = [
        topic1,
        topic2,
    ]

    result = service.search_documentation(
        "install",
    )

    assert len(result) == 2

    assert result[0]["topic_id"] == "install"
    assert result[1]["topic_id"] == "upgrade"

    assert repository.update_documentation_view_count.call_count == 2

    repository.update_documentation_view_count.assert_any_call(
        "install",
    )

    repository.update_documentation_view_count.assert_any_call(
        "upgrade",
    )


def test_search_documentation_with_category(
    documentation_service,
):
    """Category parameter should not affect repository search."""

    service, _, repository, _ = documentation_service

    repository.search_documentation.return_value = []

    service.search_documentation(
        "database",
        category="admin",
    )

    repository.search_documentation.assert_called_once_with(
        "database",
        limit=20,
    )