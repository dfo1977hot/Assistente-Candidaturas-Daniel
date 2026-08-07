from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from acd.application.platform.services.configuration_service import (
    ConfigurationService,
)


@pytest.fixture
def configuration_service(monkeypatch):
    """
    Creates ConfigurationService with mocked dependencies.
    """

    session = MagicMock()

    repository = MagicMock()

    provider = MagicMock()

    logger = MagicMock()

    operation = MagicMock()
    operation.__enter__.return_value = None
    operation.__exit__.return_value = None

    logger.operation.return_value = operation

    monkeypatch.setattr(
        "acd.application.platform.services.configuration_service.PlatformRepository",
        lambda session: repository,
    )

    monkeypatch.setattr(
        "acd.application.platform.services.configuration_service.StructuredLogger",
        lambda name: logger,
    )

    monkeypatch.setattr(
        "acd.application.platform.services.configuration_service.get_provider",
        lambda: provider,
    )

    service = ConfigurationService(session)

    return (
        service,
        repository,
        provider,
        session,
    )


def create_config(
    *,
    key="setting",
    value="abc",
    config_type="string",
    category="system",
    description="desc",
    validation_rules=None,
    default_value=None,
    is_secret=False,
):
    config = SimpleNamespace(
        key=key,
        value=value,
        config_type=config_type,
        category=category,
        description=description,
        validation_rules=validation_rules,
        default_value=default_value,
        is_secret=is_secret,
    )

    config.get_typed_value = MagicMock(
        return_value=value,
    )

    return config


def test_get_config_from_provider(configuration_service):
    service, repository, provider, _ = configuration_service

    provider.get.return_value = "provider-value"

    result = service.get_config("my.key")

    assert result == "provider-value"

    repository.get_config.assert_not_called()


def test_get_config_from_repository(configuration_service):
    service, repository, provider, _ = configuration_service

    provider.get.return_value = None

    repository.get_config.return_value = create_config(
        value="repository-value",
    )

    result = service.get_config("my.key")

    assert result == "repository-value"

    repository.get_config.assert_called_once_with(
        "my.key",
    )


def test_get_config_default_value(configuration_service):
    service, repository, provider, _ = configuration_service

    provider.get.return_value = None

    repository.get_config.return_value = None

    result = service.get_config(
        "missing",
        default="default",
    )

    assert result == "default"


def test_set_config(configuration_service):
    service, repository, provider, _ = configuration_service

    repository.set_config.return_value = create_config(
        key="theme",
        value="dark",
    )

    result = service.set_config(
        "theme",
        "dark",
    )

    assert result["key"] == "theme"
    assert result["value"] == "dark"

    provider.set.assert_called_once_with(
        "theme",
        "dark",
    )


def test_get_section(configuration_service):
    service, repository, _, _ = configuration_service

    repository.get_all_configs.return_value = [
        create_config(
            key="a",
            value=1,
        ),
        create_config(
            key="b",
            value=2,
        ),
    ]

    result = service.get_section(
        "system",
    )

    assert result == {
        "a": 1,
        "b": 2,
    }

    repository.get_all_configs.assert_called_once_with(
        category="system",
    )


def test_get_all_configs(configuration_service):
    service, repository, _, _ = configuration_service

    repository.get_all_configs.return_value = [
        create_config(
            key="one",
            value=1,
        ),
        create_config(
            key="two",
            value=2,
        ),
    ]

    result = service.get_all_configs()

    assert result == {
        "one": 1,
        "two": 2,
    }

    repository.get_all_configs.assert_called_once_with()


def test_validate_config_without_rules(configuration_service):
    service, repository, _, _ = configuration_service

    repository.get_config.return_value = None

    assert service.validate_config(
        "setting",
        "value",
    ) is True


def test_validate_config_without_validation_rules(configuration_service):
    service, repository, _, _ = configuration_service

    repository.get_config.return_value = create_config(
        validation_rules=None,
    )

    assert service.validate_config(
        "setting",
        "value",
    ) is True


def test_validate_config_pattern_success(configuration_service):
    service, repository, _, _ = configuration_service

    repository.get_config.return_value = create_config(
        validation_rules={
            "pattern": r"^[a-z]+$",
        },
    )

    assert service.validate_config(
        "setting",
        "abc",
    ) is True


def test_validate_config_pattern_failure(configuration_service):
    service, repository, _, _ = configuration_service

    repository.get_config.return_value = create_config(
        validation_rules={
            "pattern": r"^[a-z]+$",
        },
    )

    assert service.validate_config(
        "setting",
        "123",
    ) is False


def test_validate_config_integer_success(configuration_service):
    service, repository, _, _ = configuration_service

    repository.get_config.return_value = create_config(
        config_type="integer",
        validation_rules={
            "min": 10,
            "max": 20,
        },
    )

    assert service.validate_config(
        "threads",
        15,
    ) is True


def test_validate_config_integer_below_min(configuration_service):
    service, repository, _, _ = configuration_service

    repository.get_config.return_value = create_config(
        config_type="integer",
        validation_rules={
            "min": 10,
        },
    )

    assert service.validate_config(
        "threads",
        5,
    ) is False


def test_validate_config_integer_above_max(configuration_service):
    service, repository, _, _ = configuration_service

    repository.get_config.return_value = create_config(
        config_type="integer",
        validation_rules={
            "max": 20,
        },
    )

    assert service.validate_config(
        "threads",
        30,
    ) is False


def test_validate_config_integer_invalid_value(configuration_service):
    service, repository, _, _ = configuration_service

    repository.get_config.return_value = create_config(
        config_type="integer",
        validation_rules={
            "min": 1,
        },
    )

    assert service.validate_config(
        "threads",
        "abc",
    ) is False


def test_validate_config_integer_none(configuration_service):
    service, repository, _, _ = configuration_service

    repository.get_config.return_value = create_config(
        config_type="integer",
        validation_rules={
            "min": 1,
        },
    )

    assert service.validate_config(
        "threads",
        None,
    ) is False


def test_validate_config_pattern_and_integer(configuration_service):
    service, repository, _, _ = configuration_service

    repository.get_config.return_value = create_config(
        config_type="integer",
        validation_rules={
            "pattern": r"^\d+$",
            "min": 1,
            "max": 100,
        },
    )

    assert service.validate_config(
        "threads",
        "50",
    ) is True

def test_export_config(configuration_service):
    service, repository, _, _ = configuration_service

    repository.get_all_configs.return_value = [
        create_config(
            key="host",
            value="localhost",
        ),
        create_config(
            key="port",
            value=5432,
        ),
    ]

    result = service.export_config()

    assert result["host"]["value"] == "localhost"
    assert result["host"]["type"] == "string"
    assert result["host"]["category"] == "system"

    assert result["port"]["value"] == 5432


def test_export_config_secret(configuration_service):
    service, repository, _, _ = configuration_service

    repository.get_all_configs.return_value = [
        create_config(
            key="password",
            value="super-secret",
            is_secret=True,
        )
    ]

    result = service.export_config()

    assert result["password"]["value"] == "***"
    assert result["password"]["is_secret"] is True


def test_export_config_empty(configuration_service):
    service, repository, _, _ = configuration_service

    repository.get_all_configs.return_value = []

    result = service.export_config()

    assert result == {}


def test_reset_to_defaults(configuration_service):
    service, repository, _, session = configuration_service

    config1 = create_config(
        default_value="default1",
    )

    config2 = create_config(
        default_value="default2",
    )

    repository.get_all_configs.return_value = [
        config1,
        config2,
    ]

    result = service.reset_to_defaults()

    assert result["reset_count"] == 2
    assert result["category"] is None

    assert config1.value == "default1"
    assert config2.value == "default2"

    session.commit.assert_called_once()


def test_reset_to_defaults_category(configuration_service):
    service, repository, _, session = configuration_service

    config = create_config(
        default_value="abc",
    )

    repository.get_all_configs.return_value = [
        config,
    ]

    result = service.reset_to_defaults(
        "network",
    )

    assert result["reset_count"] == 1
    assert result["category"] == "network"

    repository.get_all_configs.assert_called_once_with(
        category="network",
    )

    session.commit.assert_called_once()


def test_reset_to_defaults_without_default_value(configuration_service):
    service, repository, _, session = configuration_service

    config = create_config(
        default_value=None,
    )

    original = config.value

    repository.get_all_configs.return_value = [
        config,
    ]

    result = service.reset_to_defaults()

    assert result["reset_count"] == 0
    assert config.value == original

    session.commit.assert_called_once()


def test_reset_to_defaults_mixed(configuration_service):
    service, repository, _, session = configuration_service

    config1 = create_config(
        default_value="default",
    )

    config2 = create_config(
        default_value=None,
    )

    repository.get_all_configs.return_value = [
        config1,
        config2,
    ]

    result = service.reset_to_defaults()

    assert result["reset_count"] == 1

    assert config1.value == "default"

    session.commit.assert_called_once()


def test_export_config_preserves_metadata(configuration_service):
    service, repository, _, _ = configuration_service

    repository.get_all_configs.return_value = [
        create_config(
            key="timeout",
            value=30,
            config_type="integer",
            category="network",
            description="Request timeout",
            is_secret=False,
        )
    ]

    exported = service.export_config()

    timeout = exported["timeout"]

    assert timeout["value"] == 30
    assert timeout["type"] == "integer"
    assert timeout["category"] == "network"
    assert timeout["description"] == "Request timeout"
    assert timeout["is_secret"] is False