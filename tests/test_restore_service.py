from __future__ import annotations

from datetime import datetime
import hashlib
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from acd.application.platform.services.restore_service import (
    RestoreService,
)
from acd.domain.platform.backup import BackupStatus


@pytest.fixture
def restore_service(monkeypatch, tmp_path):
    """
    Creates RestoreService with mocked dependencies.
    """

    session = MagicMock()

    repository = MagicMock()

    logger = MagicMock()

    operation = MagicMock()
    operation.__enter__.return_value = None
    operation.__exit__.return_value = None

    logger.operation.return_value = operation

    monkeypatch.setattr(
        "acd.application.platform.services.restore_service.PlatformRepository",
        lambda session: repository,
    )

    monkeypatch.setattr(
        "acd.application.platform.services.restore_service.StructuredLogger",
        lambda name: logger,
    )

    database = tmp_path / "acd.db"
    database.write_text("database")

    service = RestoreService(
        session,
        database_path=str(database),
    )

    return (
        service,
        repository,
        tmp_path,
    )


def create_backup(
    *,
    id=1,
    checksum="checksum",
):
    return SimpleNamespace(
        id=id,
        name=f"backup_{id}",
        backup_type="MANUAL",
        status=BackupStatus.COMPLETED.value,
        file_path="backup_path",
        file_size_mb=1.5,
        checksum=checksum,
        created_at=datetime(2026, 1, 1, 12, 0, 0),
    )


def test_restore_from_backup_success(
    restore_service,
    tmp_path,
):
    service, repository, _ = restore_service

    backup_dir = tmp_path / "backup"

    backup_dir.mkdir()

    db = backup_dir / "database.db"
    db.write_bytes(b"backup")

    checksum = hashlib.sha256(b"backup").hexdigest()

    backup = create_backup(
        checksum=checksum,
    )

    backup.file_path = str(backup_dir)

    repository.list_backups.return_value = [
        backup,
    ]

    result = service.restore_from_backup(
        backup.id,
    )

    assert result["backup_id"] == backup.id

    repository.update_backup_status.assert_called_once_with(
        backup.id,
        BackupStatus.RESTORED.value,
    )


def test_restore_from_backup_without_verify(
    restore_service,
):
    service, repository, _ = restore_service

    backup = create_backup()

    repository.list_backups.return_value = [
        backup,
    ]

    service._verify_backup = MagicMock(
        return_value=False,
    )

    service.restore_from_backup(
        backup.id,
        verify=False,
    )

    service._verify_backup.assert_not_called()


def test_restore_backup_not_found(
    restore_service,
):
    service, repository, _ = restore_service

    repository.list_backups.return_value = []

    with pytest.raises(ValueError):
        service.restore_from_backup(
            999,
        )


def test_restore_backup_invalid_checksum(
    restore_service,
):
    service, repository, _ = restore_service

    backup = create_backup()

    repository.list_backups.return_value = [
        backup,
    ]

    service._verify_backup = MagicMock(
        return_value=False,
    )

    with pytest.raises(ValueError):
        service.restore_from_backup(
            backup.id,
        )


def test_verify_backup_success(
    restore_service,
    tmp_path,
):
    service, _, _ = restore_service

    backup_dir = tmp_path / "backup"

    backup_dir.mkdir()

    file = backup_dir / "database.db"
    file.write_bytes(b"backup-data")

    checksum = hashlib.sha256(
        b"backup-data"
    ).hexdigest()

    backup = create_backup(
        checksum=checksum,
    )

    backup.file_path = str(backup_dir)

    assert service._verify_backup(
        backup,
    ) is True


def test_verify_backup_invalid_checksum(
    restore_service,
    tmp_path,
):
    service, _, _ = restore_service

    backup_dir = tmp_path / "backup"

    backup_dir.mkdir()

    file = backup_dir / "database.db"
    file.write_bytes(b"backup-data")

    backup = create_backup(
        checksum="invalid",
    )

    backup.file_path = str(backup_dir)

    assert service._verify_backup(
        backup,
    ) is False


def test_verify_backup_directory_not_exists(
    restore_service,
):
    service, _, _ = restore_service

    backup = create_backup()

    backup.file_path = "directory_that_does_not_exist"

    assert service._verify_backup(
        backup,
    ) is False


def test_verify_backup_multiple_files(
    restore_service,
    tmp_path,
):
    service, _, _ = restore_service

    backup_dir = tmp_path / "backup"

    backup_dir.mkdir()

    (backup_dir / "a.txt").write_bytes(
        b"abc"
    )

    (backup_dir / "b.txt").write_bytes(
        b"def"
    )

    checksum = hashlib.sha256()

    checksum.update(b"abc")
    checksum.update(b"def")

    backup = create_backup(
        checksum=checksum.hexdigest(),
    )

    backup.file_path = str(backup_dir)

    assert service._verify_backup(
        backup,
    ) is True


def test_verify_backup_empty_directory(
    restore_service,
    tmp_path,
):
    service, _, _ = restore_service

    backup_dir = tmp_path / "empty"

    backup_dir.mkdir()

    backup = create_backup(
        checksum=hashlib.sha256().hexdigest(),
    )

    backup.file_path = str(backup_dir)

    assert service._verify_backup(
        backup,
    ) is True


def test_get_restore_point(
    restore_service,
):
    service, repository, _ = restore_service

    backup = create_backup(
        id=10,
    )

    repository.list_backups.return_value = [
        backup,
    ]

    service._verify_backup = MagicMock(
        return_value=True,
    )

    result = service.get_restore_point(
        10,
    )

    assert result["id"] == 10
    assert result["name"] == backup.name
    assert result["is_valid"] is True


def test_get_restore_point_not_found(
    restore_service,
):
    service, repository, _ = restore_service

    repository.list_backups.return_value = []

    assert service.get_restore_point(
        999,
    ) is None


def test_list_restore_points(
    restore_service,
):
    service, repository, _ = restore_service

    backup1 = create_backup(id=1)
    backup2 = create_backup(id=2)

    repository.list_backups.return_value = [
        backup1,
        backup2,
    ]

    service._verify_backup = MagicMock(
        side_effect=[
            True,
            False,
        ]
    )

    result = service.list_restore_points()

    assert len(result) == 2

    assert result[0]["id"] == 1
    assert result[0]["is_valid"] is True

    assert result[1]["id"] == 2
    assert result[1]["is_valid"] is False

    repository.list_backups.assert_called_once_with(
        status=BackupStatus.COMPLETED.value,
    )


def test_list_restore_points_empty(
    restore_service,
):
    service, repository, _ = restore_service

    repository.list_backups.return_value = []

    result = service.list_restore_points()

    assert result == []


def test_list_restore_points_without_created_at(
    restore_service,
):
    service, repository, _ = restore_service

    backup = create_backup(id=3)
    backup.created_at = None

    repository.list_backups.return_value = [
        backup,
    ]

    service._verify_backup = MagicMock(
        return_value=True,
    )

    result = service.list_restore_points()

    assert result[0]["created_at"] is None
    assert result[0]["is_valid"] is True


def test_get_restore_point_without_created_at(
    restore_service,
):
    service, repository, _ = restore_service

    backup = create_backup(id=5)
    backup.created_at = None

    repository.list_backups.return_value = [
        backup,
    ]

    service._verify_backup = MagicMock(
        return_value=False,
    )

    result = service.get_restore_point(5)

    assert result["created_at"] is None
    assert result["is_valid"] is False


def test_restore_from_backup_without_database_file(
    restore_service,
    tmp_path,
):
    service, repository, _ = restore_service

    backup_dir = tmp_path / "backup"

    backup_dir.mkdir()

    backup = create_backup(id=20)
    backup.file_path = str(backup_dir)

    repository.list_backups.return_value = [
        backup,
    ]

    service._verify_backup = MagicMock(
        return_value=True,
    )

    result = service.restore_from_backup(
        20,
    )

    assert result["backup_id"] == 20

    repository.update_backup_status.assert_called_once_with(
        20,
        BackupStatus.RESTORED.value,
    )


def test_restore_from_backup_without_backup_directory(
    restore_service,
):
    service, repository, _ = restore_service

    backup = create_backup(id=30)
    backup.file_path = "directory_that_does_not_exist"

    repository.list_backups.return_value = [
        backup,
    ]

    service._verify_backup = MagicMock(
        return_value=True,
    )

    result = service.restore_from_backup(
        30,
    )

    assert result["backup_id"] == 30


def test_restore_from_backup_returns_expected_keys(
    restore_service,
):
    service, repository, _ = restore_service

    backup = create_backup(id=40)

    repository.list_backups.return_value = [
        backup,
    ]

    service._verify_backup = MagicMock(
        return_value=True,
    )

    result = service.restore_from_backup(
        40,
    )

    assert {
        "backup_id",
        "name",
        "restored_at",
        "database_path",
    }.issubset(result.keys())