from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from acd.application.release.services.update_service import UpdateService


@pytest.fixture
def update_service(monkeypatch):
    """Create UpdateService with mocked dependencies."""

    session = MagicMock()
    repository = MagicMock()
    logger = MagicMock()

    operation = MagicMock()
    operation.__enter__.return_value = None
    operation.__exit__.return_value = None
    logger.operation.return_value = operation

    monkeypatch.setattr(
        "acd.application.release.services.update_service.ReleaseRepository",
        lambda session: repository,
    )
    monkeypatch.setattr(
        "acd.application.release.services.update_service.StructuredLogger",
        lambda name: logger,
    )

    service = UpdateService(session, "database.db")

    return service, session, repository, logger


def make_version(major: int, minor: int, patch: int):
    """Create a lightweight comparable version object."""

    return SimpleNamespace(major=major, minor=minor, patch=patch)


def make_release(
    version: str,
    *,
    critical: bool = False,
):
    """Create a fake release object."""

    release = MagicMock()
    release.version = version
    release.is_critical = critical
    release.to_dict.return_value = {
        "version": version,
        "critical": critical,
    }
    return release


def make_update_history(update_id: int = 10):
    """Create a fake update history object."""

    update = MagicMock()
    update.id = update_id
    update.from_version = "1.0.0"
    update.to_version = "2.0.0"
    update.rollback_available = True
    update.status = "completed"
    update.update_date.isoformat.return_value = "2026-01-01T12:00:00"
    update.can_rollback.return_value = True
    update.to_dict.return_value = {
        "id": update_id,
        "from_version": "1.0.0",
        "to_version": "2.0.0",
    }
    return update


def test_service_creation(update_service):
    """Service should initialize correctly."""

    service, session, repository, logger = update_service

    assert service.session is session
    assert service.repository is repository
    assert service.logger is logger
    assert service.database_path == "database.db"


def test_check_for_updates_without_release(update_service):
    """No release available."""

    service, _, repository, _ = update_service
    repository.get_latest_stable_release.return_value = None

    result = service.check_for_updates("1.0.0")

    assert result == {
        "update_available": False,
        "current_version": "1.0.0",
        "latest_version": None,
        "latest_release": None,
        "is_critical": False,
    }


def test_check_for_updates_available(update_service, monkeypatch):
    """Stable update available."""

    service, _, repository, _ = update_service

    repository.get_latest_stable_release.return_value = make_release(
        "2.0.0",
        critical=True,
    )

    monkeypatch.setattr(
        "acd.application.release.services.update_service.VersionManager.parse_version",
        lambda version: (int(version.split(".")[0]), int(version.split(".")[1]), int(version.split(".")[2])),
    )

    result = service.check_for_updates("1.0.0")

    assert result["update_available"] is True
    assert result["current_version"] == "1.0.0"
    assert result["latest_version"] == "2.0.0"
    assert result["latest_release"] == {
        "version": "2.0.0",
        "critical": True,
    }
    assert result["is_critical"] is True


def test_check_for_updates_not_available(update_service, monkeypatch):
    """Current version is already latest."""

    service, _, repository, _ = update_service

    repository.get_latest_stable_release.return_value = make_release("1.0.0")

    monkeypatch.setattr(
        "acd.application.release.services.update_service.VersionManager.parse_version",
        lambda version: (int(version.split(".")[0]), int(version.split(".")[1]), int(version.split(".")[2])),
    )

    result = service.check_for_updates("1.0.0")

    assert result["update_available"] is False
    assert result["latest_version"] is None
    assert result["latest_release"] is None
    assert result["is_critical"] is False


def test_check_for_updates_beta(update_service, monkeypatch):
    """Beta release should be selected when newer."""

    service, _, repository, _ = update_service

    repository.get_latest_stable_release.return_value = make_release("2.0.0")
    repository.get_latest_beta_release.return_value = make_release("2.1.0", critical=True)

    monkeypatch.setattr(
        "acd.application.release.services.update_service.VersionManager.parse_version",
        lambda version: (int(version.split(".")[0]), int(version.split(".")[1]), int(version.split(".")[2])),
    )

    result = service.check_for_updates("1.0.0", include_beta=True)

    assert result["update_available"] is True
    assert result["latest_version"] == "2.1.0"
    assert result["is_critical"] is True


def test_check_for_updates_exception(update_service, monkeypatch):
    """Exceptions must be handled."""

    service, _, _, logger = update_service

    monkeypatch.setattr(
        "acd.application.release.services.update_service.VersionManager.parse_version",
        MagicMock(side_effect=RuntimeError("parser failure")),
    )

    result = service.check_for_updates("1.0.0")

    assert result == {
        "update_available": False,
        "current_version": "1.0.0",
        "latest_version": None,
        "latest_release": None,
        "is_critical": False,
    }

    logger.error.assert_called_once()


def test_prepare_update_patch_without_backup(
    update_service,
    monkeypatch,
):
    """Prepare PATCH update without database backup."""

    service, _, repository, _ = update_service

    repository.create_update_history.return_value = (
        make_update_history()
    )

    versions = {
        "1.0.0": make_version(1, 0, 0),
        "1.0.1": make_version(1, 0, 1),
    }

    monkeypatch.setattr(
        "acd.application.release.services.update_service.VersionManager.parse_version",
        lambda version: versions[version],
    )

    result = service.prepare_update(
        "1.0.0",
        "1.0.1",
    )

    assert result["success"] is True
    assert result["update_id"] == 10
    assert result["backup_path"] is None

    repository.create_update_history.assert_called_once_with(
        from_version="1.0.0",
        to_version="1.0.1",
        update_type="PATCH",
        is_automatic=False,
    )


def test_prepare_update_minor(
    update_service,
    monkeypatch,
):
    """Prepare MINOR update."""

    service, _, repository, _ = update_service

    repository.create_update_history.return_value = (
        make_update_history()
    )

    versions = {
        "1.0.0": make_version(1, 0, 0),
        "1.1.0": make_version(1, 1, 0),
    }

    monkeypatch.setattr(
        "acd.application.release.services.update_service.VersionManager.parse_version",
        lambda version: versions[version],
    )

    result = service.prepare_update(
        "1.0.0",
        "1.1.0",
    )

    assert result["success"] is True

    repository.create_update_history.assert_called_once_with(
        from_version="1.0.0",
        to_version="1.1.0",
        update_type="MINOR",
        is_automatic=False,
    )


def test_prepare_update_major(
    update_service,
    monkeypatch,
):
    """Prepare MAJOR update."""

    service, _, repository, _ = update_service

    repository.create_update_history.return_value = (
        make_update_history()
    )

    versions = {
        "1.9.0": make_version(1, 9, 0),
        "2.0.0": make_version(2, 0, 0),
    }

    monkeypatch.setattr(
        "acd.application.release.services.update_service.VersionManager.parse_version",
        lambda version: versions[version],
    )

    result = service.prepare_update(
        "1.9.0",
        "2.0.0",
    )

    assert result["success"] is True

    repository.create_update_history.assert_called_once_with(
        from_version="1.9.0",
        to_version="2.0.0",
        update_type="MAJOR",
        is_automatic=False,
    )


def test_prepare_update_with_backup(
    update_service,
    monkeypatch,
    tmp_path,
):
    """Database backup should be created."""

    service, _, repository, _ = update_service

    db_file = tmp_path / "database.db"
    db_file.write_text("database")

    service.database_path = str(db_file)

    repository.create_update_history.return_value = (
        make_update_history()
    )

    versions = {
        "1.0.0": make_version(1, 0, 0),
        "1.0.1": make_version(1, 0, 1),
    }

    monkeypatch.setattr(
        "acd.application.release.services.update_service.VersionManager.parse_version",
        lambda version: versions[version],
    )

    copy_mock = MagicMock()

    monkeypatch.setattr(
        "acd.application.release.services.update_service.shutil.copy2",
        copy_mock,
    )

    result = service.prepare_update(
        "1.0.0",
        "1.0.1",
    )

    assert result["success"] is True
    assert result["backup_path"] is not None

    copy_mock.assert_called_once()


def test_prepare_update_repository_exception(
    update_service,
    monkeypatch,
):
    """Repository exceptions should be handled."""

    service, _, repository, logger = update_service

    repository.create_update_history.side_effect = RuntimeError(
        "database failure",
    )

    versions = {
        "1.0.0": make_version(1, 0, 0),
        "1.0.1": make_version(1, 0, 1),
    }

    monkeypatch.setattr(
        "acd.application.release.services.update_service.VersionManager.parse_version",
        lambda version: versions[version],
    )

    result = service.prepare_update(
        "1.0.0",
        "1.0.1",
    )

    assert result["success"] is False
    assert "database failure" in result["message"]

    logger.error.assert_called_once()


def test_prepare_update_invalid_version(
    update_service,
    monkeypatch,
):
    """Invalid versions should fail."""

    service, _, _, logger = update_service

    monkeypatch.setattr(
        "acd.application.release.services.update_service.VersionManager.parse_version",
        MagicMock(
            side_effect=ValueError(
                "invalid version",
            )
        ),
    )

    result = service.prepare_update(
        "abc",
        "1.0.0",
    )

    assert result["success"] is False
    assert "invalid version" in result["message"]

    logger.error.assert_called_once()


def test_complete_update_success(update_service):
    """Complete update successfully."""

    service, _, repository, _ = update_service

    repository.update_history_status.return_value = True

    result = service.complete_update(
        update_id=10,
        from_version="1.0.0",
        to_version="1.0.1",
        duration_minutes=5,
    )

    assert result is True

    repository.update_history_status.assert_called_once_with(
        10,
        status="completed",
        duration_minutes=5,
    )


def test_complete_update_failure(update_service):
    """Repository reports failure."""

    service, _, repository, _ = update_service

    repository.update_history_status.return_value = False

    result = service.complete_update(
        10,
        "1.0.0",
        "1.0.1",
        5,
    )

    assert result is False


def test_fail_update_success(update_service):
    """Fail update."""

    service, _, repository, _ = update_service

    repository.update_history_status.return_value = True

    result = service.fail_update(
        10,
        "migration failed",
        duration_minutes=2,
    )

    assert result is True

    repository.update_history_status.assert_called_once_with(
        10,
        status="failed",
        duration_minutes=2,
        error_message="migration failed",
    )


def test_fail_update_default_duration(update_service):
    """Default duration should be zero."""

    service, _, repository, _ = update_service

    repository.update_history_status.return_value = True

    service.fail_update(
        10,
        "failure",
    )

    repository.update_history_status.assert_called_once_with(
        10,
        status="failed",
        duration_minutes=0,
        error_message="failure",
    )


def test_rollback_update_not_found(update_service):
    """Update record not found."""

    service, session, _, _ = update_service

    session.query.return_value.filter_by.return_value.first.return_value = None

    result = service.rollback_update(
        99,
        "1.0.0",
    )

    assert result == {
        "success": False,
        "message": "Update record not found",
        "rolled_back_to": None,
    }


def test_rollback_update_not_completed(update_service):
    """Rollback only works for completed updates."""

    service, session, _, _ = update_service

    update = make_update_history()
    update.status = "running"

    session.query.return_value.filter_by.return_value.first.return_value = update

    result = service.rollback_update(
        10,
        "1.0.0",
    )

    assert result == {
        "success": False,
        "message": "Can only rollback completed updates",
        "rolled_back_to": None,
    }


def test_rollback_update_not_available(update_service):
    """Rollback unavailable."""

    service, session, _, _ = update_service

    update = make_update_history()
    update.rollback_available = False

    session.query.return_value.filter_by.return_value.first.return_value = update

    result = service.rollback_update(
        10,
        "1.0.0",
    )

    assert result == {
        "success": False,
        "message": "Rollback not available for this update",
        "rolled_back_to": None,
    }


def test_rollback_update_success(update_service):
    """Rollback succeeds."""

    service, session, _, logger = update_service

    update = make_update_history()

    session.query.return_value.filter_by.return_value.first.return_value = update

    result = service.rollback_update(
        10,
        "1.0.0",
    )

    assert result == {
        "success": True,
        "message": "Rolled back to 1.0.0",
        "rolled_back_to": "1.0.0",
    }

    assert update.status == "rolled_back"

    session.commit.assert_called_once()

    logger.info.assert_called_once()


def test_rollback_update_exception(update_service):
    """Exceptions during rollback."""

    service, session, _, logger = update_service

    session.query.side_effect = RuntimeError(
        "database failure",
    )

    result = service.rollback_update(
        10,
        "1.0.0",
    )

    assert result["success"] is False
    assert "database failure" in result["message"]
    assert result["rolled_back_to"] is None

    logger.error.assert_called_once()


def test_get_update_history_empty(update_service):
    """No update history."""

    service, _, repository, _ = update_service

    repository.list_update_history.return_value = []

    result = service.get_update_history()

    assert result == []

    repository.list_update_history.assert_called_once_with(
        limit=20,
    )


def test_get_update_history(update_service):
    """Return update history."""

    service, _, repository, _ = update_service

    update1 = make_update_history(1)
    update2 = make_update_history(2)

    repository.list_update_history.return_value = [
        update1,
        update2,
    ]

    result = service.get_update_history(limit=5)

    assert len(result) == 2

    assert result[0]["id"] == 1
    assert result[1]["id"] == 2

    repository.list_update_history.assert_called_once_with(
        limit=5,
    )


def test_get_rollback_options_empty(update_service):
    """No rollback options."""

    service, _, repository, _ = update_service

    repository.list_update_history.return_value = []

    result = service.get_rollback_options()

    assert result == []

    repository.list_update_history.assert_called_once_with(
        status="completed",
        limit=10,
    )


def test_get_rollback_options(update_service):
    """Only rollback-capable updates should be returned."""

    service, _, repository, _ = update_service

    rollback_ok = make_update_history(1)

    rollback_no = make_update_history(2)
    rollback_no.can_rollback.return_value = False

    repository.list_update_history.return_value = [
        rollback_ok,
        rollback_no,
    ]

    result = service.get_rollback_options()

    assert len(result) == 1

    option = result[0]

    assert option["update_id"] == 1
    assert option["from_version"] == "1.0.0"
    assert option["to_version"] == "2.0.0"
    assert option["can_rollback"] is True


def test_get_rollback_options_all_invalid(update_service):
    """All completed updates without rollback."""

    service, _, repository, _ = update_service

    updates = []

    for i in range(3):
        update = make_update_history(i + 1)
        update.can_rollback.return_value = False
        updates.append(update)

    repository.list_update_history.return_value = updates

    result = service.get_rollback_options()

    assert result == []


def test_get_rollback_options_all_valid(update_service):
    """All updates allow rollback."""

    service, _, repository, _ = update_service

    updates = [
        make_update_history(1),
        make_update_history(2),
        make_update_history(3),
    ]

    repository.list_update_history.return_value = updates

    result = service.get_rollback_options()

    assert len(result) == 3

    assert result[0]["update_id"] == 1
    assert result[1]["update_id"] == 2
    assert result[2]["update_id"] == 3