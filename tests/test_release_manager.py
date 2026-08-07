from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from acd.application.release.release_manager import ReleaseManager


@pytest.fixture
def release_manager(monkeypatch):
    """Create ReleaseManager with mocked dependencies."""

    session = MagicMock()

    repository = MagicMock()
    logger = MagicMock()

    installation_service = MagicMock()
    update_service = MagicMock()
    migration_service = MagicMock()
    documentation_service = MagicMock()
    feature_flags = MagicMock()
    plugin_loader = MagicMock()

    monkeypatch.setattr(
        "acd.application.release.release_manager.ReleaseRepository",
        lambda session: repository,
    )

    monkeypatch.setattr(
        "acd.application.release.release_manager.StructuredLogger",
        lambda name: logger,
    )

    monkeypatch.setattr(
        "acd.application.release.release_manager.InstallationService",
        lambda session, path: installation_service,
    )

    monkeypatch.setattr(
        "acd.application.release.release_manager.UpdateService",
        lambda session, db: update_service,
    )

    monkeypatch.setattr(
        "acd.application.release.release_manager.MigrationService",
        lambda session: migration_service,
    )

    monkeypatch.setattr(
        "acd.application.release.release_manager.DocumentationService",
        lambda session: documentation_service,
    )

    monkeypatch.setattr(
        "acd.application.release.release_manager.FeatureFlagService",
        lambda session: feature_flags,
    )

    monkeypatch.setattr(
        "acd.application.release.release_manager.get_plugin_loader",
        lambda: plugin_loader,
    )

    manager = ReleaseManager(session)

    return (
        manager,
        session,
        repository,
        logger,
        installation_service,
        update_service,
        migration_service,
        documentation_service,
        feature_flags,
        plugin_loader,
    )


def test_release_manager_creation(
    release_manager,
):
    """ReleaseManager initialization."""

    (
        manager,
        session,
        repository,
        logger,
        installation_service,
        update_service,
        migration_service,
        documentation_service,
        feature_flags,
        plugin_loader,
    ) = release_manager

    assert manager.session is session
    assert manager.repository is repository
    assert manager.logger is logger
    assert manager.installation_service is installation_service
    assert manager.update_service is update_service
    assert manager.migration_service is migration_service
    assert manager.documentation_service is documentation_service
    assert manager.feature_flags is feature_flags
    assert manager.plugin_loader is plugin_loader

def test_get_system_status_not_installed(
    release_manager,
):
    """System not installed."""

    (
        manager,
        _,
        repository,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = release_manager

    repository.get_installed_version.return_value = None

    result = manager.get_system_status()

    assert result == {
        "installed": False,
        "version": None,
        "status": "not_installed",
    }


def test_get_system_status_installed(
    release_manager,
    monkeypatch,
):
    """Installed system without updates."""

    (
        manager,
        _,
        repository,
        _,
        _,
        _,
        _,
        _,
        feature_flags,
        _,
    ) = release_manager

    installed = MagicMock()
    installed.current_version = "1.0.0"
    installed.installation_path = "./acd"
    installed.status = "active"
    installed.is_beta = False

    from datetime import datetime

    installed.installation_date = datetime(2026, 1, 1)

    repository.get_installed_version.return_value = installed
    repository.get_latest_stable_release.return_value = None
    repository.get_latest_beta_release.return_value = None

    feature_flags.get_all_flags.return_value = {}

    monkeypatch.setattr(
        "acd.application.release.release_manager.VersionManager.compare_versions",
        lambda *_: 0,
    )

    result = manager.get_system_status()

    assert result["installed"] is True
    assert result["current_version"] == "1.0.0"
    assert result["updates_available"] is False
    assert result["latest_available_version"] is None
    assert result["features"] == {}


def test_get_system_status_exception(
    release_manager,
):
    """Unexpected exception."""

    (
        manager,
        _,
        repository,
        logger,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = release_manager

    repository.get_installed_version.side_effect = RuntimeError(
        "database failure",
    )

    result = manager.get_system_status()

    assert result["installed"] is False
    assert "database failure" in result["error"]

    logger.error.assert_called_once()


def test_perform_installation_success(
    release_manager,
):
    """Successful installation."""

    (
        manager,
        _,
        _,
        logger,
        installation_service,
        _,
        _,
        _,
        _,
        _,
    ) = release_manager

    logger.operation.return_value.__enter__.return_value = None
    logger.operation.return_value.__exit__.return_value = None

    installation_service.perform_fresh_install.return_value = {
        "success": True,
        "message": "Installation completed",
    }

    result = manager.perform_installation(
        "1.0.0",
        "./acd",
    )

    assert result["success"] is True

    installation_service.perform_fresh_install.assert_called_once_with(
        "1.0.0",
        "./acd",
        True,
    )

    logger.info.assert_called_once()


def test_perform_installation_failure(
    release_manager,
):
    """Installation failure."""

    (
        manager,
        _,
        _,
        logger,
        installation_service,
        _,
        _,
        _,
        _,
        _,
    ) = release_manager

    logger.operation.return_value.__enter__.return_value = None
    logger.operation.return_value.__exit__.return_value = None

    installation_service.perform_fresh_install.return_value = {
        "success": False,
        "message": "Installation failed",
    }

    result = manager.perform_installation(
        "1.0.0",
        "./acd",
    )

    assert result["success"] is False

    logger.info.assert_not_called()


def test_perform_update(
    release_manager,
):
    """Successful update."""

    (
        manager,
        _,
        repository,
        logger,
        _,
        update_service,
        migration_service,
        _,
        _,
        _,
    ) = release_manager

    logger.operation.return_value.__enter__.return_value = None
    logger.operation.return_value.__exit__.return_value = None

    update_service.prepare_update.return_value = {
        "success": True,
        "update_id": 123,
        "backup_path": "/tmp/backup.zip",
    }

    migration_service.create_migration.return_value = {
        "success": True,
        "message": "Migration completed",
    }

    result = manager.perform_update(
        "1.0.0",
        "2.0.0",
    )

    assert result["success"] is True
    assert result["update_id"] == 123
    assert result["backup_path"] == "/tmp/backup.zip"

    update_service.prepare_update.assert_called_once_with(
        "1.0.0",
        "2.0.0",
    )

    migration_service.create_migration.assert_called_once_with(
        "1.0.0",
        "2.0.0",
        migration_type="database",
    )

    update_service.complete_update.assert_called_once_with(
        123,
        "1.0.0",
        "2.0.0",
        5,
    )

    repository.update_installed_version.assert_called_once_with(
        "1.0.0",
        "2.0.0",
        installation_type="upgraded",
    )

    logger.info.assert_called_once()


def test_check_for_updates_not_installed(
    release_manager,
):
    """No installed version."""

    (
        manager,
        _,
        repository,
        _,
        _,
        update_service,
        _,
        _,
        _,
        _,
    ) = release_manager

    repository.get_installed_version.return_value = None

    result = manager.check_for_updates()

    assert result == {
        "update_available": False,
    }

    update_service.check_for_updates.assert_not_called()


def test_check_for_updates(
    release_manager,
):
    """Check available updates."""

    (
        manager,
        _,
        repository,
        _,
        _,
        update_service,
        _,
        _,
        _,
        _,
    ) = release_manager

    installed = MagicMock()
    installed.current_version = "1.0.0"

    repository.get_installed_version.return_value = installed

    update_service.check_for_updates.return_value = {
        "update_available": True,
    }

    result = manager.check_for_updates(
        include_beta=True,
    )

    assert result["update_available"] is True

    update_service.check_for_updates.assert_called_once_with(
        "1.0.0",
        True,
    )


def test_rollback_not_available(
    release_manager,
):
    """Rollback unavailable."""

    (
        manager,
        _,
        repository,
        _,
        _,
        update_service,
        _,
        _,
        _,
        _,
    ) = release_manager

    repository.get_last_successful_update.return_value = None

    result = manager.rollback_to_previous()

    assert result == {
        "success": False,
        "message": "No rollback available",
    }

    update_service.rollback_update.assert_not_called()


def test_rollback_success(
    release_manager,
):
    """Rollback executed."""

    (
        manager,
        _,
        repository,
        _,
        _,
        update_service,
        _,
        _,
        _,
        _,
    ) = release_manager

    update = MagicMock()
    update.id = 15
    update.from_version = "1.0.0"
    update.can_rollback.return_value = True

    repository.get_last_successful_update.return_value = update

    update_service.rollback_update.return_value = {
        "success": True,
    }

    result = manager.rollback_to_previous()

    assert result["success"] is True

    update_service.rollback_update.assert_called_once_with(
        15,
        "1.0.0",
    )


def test_enable_feature(
    release_manager,
):
    """Enable feature."""

    (
        manager,
        *_,
        feature_flags,
        __,
    ) = release_manager

    feature_flags.enable_feature.return_value = True

    assert manager.enable_feature("new_ui") is True

    feature_flags.enable_feature.assert_called_once_with(
        "new_ui",
    )


def test_disable_feature(
    release_manager,
):
    """Disable feature."""

    (
        manager,
        *_,
        feature_flags,
        __,
    ) = release_manager

    feature_flags.disable_feature.return_value = True

    assert manager.disable_feature("new_ui") is True

    feature_flags.disable_feature.assert_called_once_with(
        "new_ui",
    )


def test_is_feature_enabled_without_installation(
    release_manager,
):
    """Feature check without installed version."""

    (
        manager,
        _,
        repository,
        _,
        _,
        _,
        _,
        _,
        feature_flags,
        _,
    ) = release_manager

    repository.get_installed_version.return_value = None

    assert manager.is_feature_enabled(
        "new_ui",
    ) is False

    feature_flags.is_enabled.assert_not_called()


def test_is_feature_enabled(
    release_manager,
):
    """Feature enabled."""

    (
        manager,
        _,
        repository,
        _,
        _,
        _,
        _,
        _,
        feature_flags,
        _,
    ) = release_manager

    installed = MagicMock()
    installed.current_version = "2.0.0"

    repository.get_installed_version.return_value = installed

    feature_flags.is_enabled.return_value = True

    assert manager.is_feature_enabled(
        "new_ui",
    ) is True

    feature_flags.is_enabled.assert_called_once_with(
        "new_ui",
        "2.0.0",
    )


def test_load_plugins(
    release_manager,
):
    """Load plugins successfully."""

    (
        manager,
        session,
        repository,
        _,
        _,
        _,
        _,
        _,
        _,
        plugin_loader,
    ) = release_manager

    installed = MagicMock()
    installed.current_version = "2.0.0"

    repository.get_installed_version.return_value = installed

    plugin_loader.discover_plugins.return_value = [
        "plugin_a",
        "plugin_b",
    ]

    plugin_loader.load_plugin.side_effect = [
        True,
        False,
    ]

    result = manager.load_plugins(
        ["plugins"],
    )

    assert result == {
        "discovered": 2,
        "loaded": 1,
        "plugins": ["plugin_a"],
    }

    plugin_loader.add_plugin_dir.assert_called_once_with(
        "plugins",
    )

    plugin_loader.set_context.assert_called_once_with(
        {
            "app_version": "2.0.0",
        }
    )

    assert plugin_loader.load_plugin.call_count == 2


def test_load_plugins_without_installed_version(
    release_manager,
):
    """Load plugins when system is not installed."""

    (
        manager,
        session,
        repository,
        _,
        _,
        _,
        _,
        _,
        _,
        plugin_loader,
    ) = release_manager

    repository.get_installed_version.return_value = None

    plugin_loader.discover_plugins.return_value = []

    result = manager.load_plugins()

    assert result == {
        "discovered": 0,
        "loaded": 0,
        "plugins": [],
    }

    from acd import get_version

    plugin_loader.set_context.assert_called_once_with(
        {
            "app_version": get_version(),
        }
    )


def test_get_release_notes_found(
    release_manager,
):
    """Release notes found."""

    (
        manager,
        _,
        repository,
        *_,
    ) = release_manager

    release = MagicMock()
    release.release_notes = "Bug fixes"

    repository.get_release.return_value = release

    result = manager.get_release_notes(
        "2.0.0",
    )

    assert result == "Bug fixes"

    repository.get_release.assert_called_once_with(
        "2.0.0",
    )


def test_get_release_notes_not_found(
    release_manager,
):
    """Release notes missing."""

    (
        manager,
        _,
        repository,
        *_,
    ) = release_manager

    repository.get_release.return_value = None

    assert manager.get_release_notes(
        "9.9.9",
    ) == ""


def test_search_help(
    release_manager,
):
    """Delegate documentation search."""

    (
        manager,
        *_,
        documentation_service,
        __,
        ___,
    ) = release_manager

    documentation_service.search_documentation.return_value = [
        {"topic_id": "install"},
    ]

    result = manager.search_help(
        "install",
    )

    assert result == [
        {"topic_id": "install"},
    ]

    documentation_service.search_documentation.assert_called_once_with(
        "install",
    )


def test_get_help_topic(
    release_manager,
):
    """Delegate help topic lookup."""

    (
        manager,
        *_,
        documentation_service,
        __,
        ___,
    ) = release_manager

    documentation_service.get_topic.return_value = {
        "topic_id": "intro",
    }

    result = manager.get_help_topic(
        "intro",
    )

    assert result == {
        "topic_id": "intro",
    }

    documentation_service.get_topic.assert_called_once_with(
        "intro",
    )


def test_get_system_overview(
    release_manager,
):
    """Complete system overview."""

    (
        manager,
        *_,
    ) = release_manager

    manager.get_system_status = MagicMock(
        return_value={"installed": True},
    )

    manager.installation_service.get_installation_info.return_value = {
        "path": "./",
    }

    manager.installation_service.check_dependencies.return_value = {
        "ok": True,
    }

    manager.installation_service.verify_installation.return_value = {
        "valid": True,
    }

    manager.update_service.get_update_history.return_value = [
        {"id": 1},
    ]

    manager.update_service.get_rollback_options.return_value = [
        {"rollback": True},
    ]

    manager.migration_service.get_migration_history.return_value = [
        {"migration": 1},
    ]

    manager.documentation_service.get_featured_topics.return_value = [
        {"topic": "intro"},
    ]

    result = manager.get_system_overview()

    assert result["status"] == {
        "installed": True,
    }

    assert result["installation_info"] == {
        "path": "./",
    }

    assert result["dependencies"] == {
        "ok": True,
    }

    assert result["verification"] == {
        "valid": True,
    }

    assert result["update_history"] == [
        {"id": 1},
    ]

    assert result["rollback_options"] == [
        {"rollback": True},
    ]

    assert result["migration_history"] == [
        {"migration": 1},
    ]

    assert result["featured_topics"] == [
        {"topic": "intro"},
    ]

    manager.update_service.get_update_history.assert_called_once_with(
        limit=10,
    )

    manager.migration_service.get_migration_history.assert_called_once_with(
        limit=10,
    )


def test_perform_update_prepare_failure(
    release_manager,
):
    """Update preparation fails."""

    (
        manager,
        _,
        repository,
        logger,
        _,
        update_service,
        migration_service,
        _,
        _,
        _,
    ) = release_manager

    logger.operation.return_value.__enter__.return_value = None
    logger.operation.return_value.__exit__.return_value = None

    update_service.prepare_update.return_value = {
        "success": False,
        "message": "Preparation failed",
    }

    result = manager.perform_update(
        "1.0.0",
        "2.0.0",
    )

    assert result == {
        "success": False,
        "message": "Preparation failed",
    }

    migration_service.create_migration.assert_not_called()
    update_service.complete_update.assert_not_called()
    repository.update_installed_version.assert_not_called()


def test_perform_update_migration_failure(
    release_manager,
):
    """Migration fails."""

    (
        manager,
        _,
        repository,
        logger,
        _,
        update_service,
        migration_service,
        _,
        _,
        _,
    ) = release_manager

    logger.operation.return_value.__enter__.return_value = None
    logger.operation.return_value.__exit__.return_value = None

    update_service.prepare_update.return_value = {
        "success": True,
        "update_id": 55,
    }

    migration_service.create_migration.return_value = {
        "success": False,
        "message": "Migration failed",
    }

    result = manager.perform_update(
        "1.0.0",
        "2.0.0",
    )

    assert result == {
        "success": False,
        "message": "Migration failed",
    }

    update_service.fail_update.assert_called_once_with(
        55,
        "Migration failed",
    )

    update_service.complete_update.assert_not_called()
    repository.update_installed_version.assert_not_called()


def test_perform_update_exception(
    release_manager,
):
    """Unexpected exception during update."""

    (
        manager,
        _,
        repository,
        logger,
        _,
        update_service,
        _,
        _,
        _,
        _,
    ) = release_manager

    logger.operation.return_value.__enter__.return_value = None
    logger.operation.return_value.__exit__.return_value = None

    update_service.prepare_update.side_effect = RuntimeError(
        "Unexpected error",
    )

    result = manager.perform_update(
        "1.0.0",
        "2.0.0",
    )

    assert result["success"] is False
    assert "Unexpected error" in result["message"]

    repository.update_installed_version.assert_not_called()
    logger.error.assert_called_once()


def test_rollback_update_cannot_rollback(
    release_manager,
):
    """Rollback object exists but cannot rollback."""

    (
        manager,
        _,
        repository,
        _,
        _,
        update_service,
        _,
        _,
        _,
        _,
    ) = release_manager

    update = MagicMock()
    update.can_rollback.return_value = False

    repository.get_last_successful_update.return_value = update

    result = manager.rollback_to_previous()

    assert result == {
        "success": False,
        "message": "No rollback available",
    }

    update_service.rollback_update.assert_not_called()


def test_get_system_status_update_available(
    release_manager,
    monkeypatch,
):
    """Installed system with newer stable release available."""

    (
        manager,
        _,
        repository,
        _,
        _,
        _,
        _,
        _,
        feature_flags,
        _,
    ) = release_manager

    from datetime import datetime

    installed = MagicMock()
    installed.current_version = "1.0.0"
    installed.installation_path = "./acd"
    installed.installation_date = datetime(2026, 1, 1)
    installed.status = "active"
    installed.is_beta = False

    stable = MagicMock()
    stable.version = "2.0.0"

    repository.get_installed_version.return_value = installed
    repository.get_latest_stable_release.return_value = stable
    repository.get_latest_beta_release.return_value = None

    feature_flags.get_all_flags.return_value = {}

    monkeypatch.setattr(
        "acd.application.release.release_manager.VersionManager.compare_versions",
        lambda *_: -1,
    )

    result = manager.get_system_status()

    assert result["updates_available"] is True
    assert result["latest_available_version"] == "2.0.0"
    assert result["latest_stable"] == "2.0.0"
