from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from acd.application.release.services.migration_service import (
    DocumentationService,
)


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
    """Create documentation topic."""

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


def test_service_creation(
    documentation_service,
):
    """Service initialization."""

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
    """Category parameter is ignored by repository."""

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


def test_get_topic_found(
    documentation_service,
):
    """Topic found."""

    service, _, repository, _ = documentation_service

    topic = make_topic("installation")

    repository.get_documentation_topic.return_value = topic

    result = service.get_topic(
        "installation",
    )

    assert result["topic_id"] == "installation"

    repository.get_documentation_topic.assert_called_once_with(
        "installation",
    )

    repository.update_documentation_view_count.assert_called_once_with(
        "installation",
    )


def test_get_topic_not_found(
    documentation_service,
):
    """Topic not found."""

    service, _, repository, _ = documentation_service

    repository.get_documentation_topic.return_value = None

    result = service.get_topic(
        "missing",
    )

    assert result is None

    repository.update_documentation_view_count.assert_not_called()


def test_get_featured_topics_empty(
    documentation_service,
):
    """No featured topics."""

    service, _, repository, _ = documentation_service

    repository.list_documentation_topics.return_value = []

    result = service.get_featured_topics()

    assert result == []

    repository.list_documentation_topics.assert_called_once_with(
        is_featured=True,
        limit=5,
    )


def test_get_featured_topics(
    documentation_service,
):
    """Featured topics."""

    service, _, repository, _ = documentation_service

    repository.list_documentation_topics.return_value = [
        make_topic("intro"),
        make_topic("upgrade"),
    ]

    result = service.get_featured_topics()

    assert len(result) == 2
    assert result[0]["topic_id"] == "intro"
    assert result[1]["topic_id"] == "upgrade"

    repository.list_documentation_topics.assert_called_once_with(
        is_featured=True,
        limit=5,
    )


def test_get_category_topics_empty(
    documentation_service,
):
    """Empty category."""

    service, _, repository, _ = documentation_service

    repository.list_documentation_topics.return_value = []

    result = service.get_category_topics(
        "database",
    )

    assert result == []

    repository.list_documentation_topics.assert_called_once_with(
        category="database",
        limit=20,
    )


def test_get_category_topics(
    documentation_service,
):
    """Topics by category."""

    service, _, repository, _ = documentation_service

    repository.list_documentation_topics.return_value = [
        make_topic("backup"),
        make_topic("restore"),
    ]

    result = service.get_category_topics(
        "database",
    )

    assert len(result) == 2
    assert result[0]["topic_id"] == "backup"
    assert result[1]["topic_id"] == "restore"

    repository.list_documentation_topics.assert_called_once_with(
        category="database",
        limit=20,
    )


def test_get_categories(
    documentation_service,
):
    """Categories come from DocumentationCategory enum."""

    service, *_ = documentation_service

    result = service.get_categories()

    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(item, str) for item in result)