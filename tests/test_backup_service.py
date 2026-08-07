from __future__ import annotations

from datetime import datetime
import hashlib
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from acd.application.platform.services.backup_service import BackupService
from acd.domain.platform.backup import BackupStatus


@pytest.fixture
def backup_service(monkeypatch, tmp_path):
    """
    Creates BackupService with mocked dependencies.
    """

    session = MagicMock()

    repository = MagicMock()

    logger = MagicMock()

    operation = MagicMock()
    operation.__enter__.return_value = None
    operation.__exit__.return_value = None

    logger.operation.return_value = operation

    monkeypatch.setattr(
        "acd.application.platform.services.backup_service.PlatformRepository",
        lambda session: repository,
    )

    monkeypatch.setattr(
        "acd.application.platform.services.backup_service.StructuredLogger",
        lambda name: logger,
    )

    database = tmp_path / "acd.db"
    database.write_text("database")

    service = BackupService(
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
    name="backup",
    status=BackupStatus.COMPLETED.value,
):
    return SimpleNamespace(
        id=id,
        name=name,
        backup_type="MANUAL",
        status=status,
        file_path="backup_path",
        file_size_mb=1.5,
        checksum="checksum",
        created_at=datetime(2026, 1, 1, 12, 0, 0),
        completed_at=datetime(2026, 1, 1, 12, 5, 0),
    )


def test_create_manual_backup(
    backup_service,
):
    service, repository, tmp_path = backup_service

    backup = create_backup(
        id=100,
    )

    repository.create_backup.return_value = backup

    result = service.create_manual_backup(
        backup_dir=str(tmp_path),
    )

    assert result["backup_id"] == 100

    repository.create_backup.assert_called_once()

    repository.update_backup_status.assert_called_once_with(
        100,
        BackupStatus.COMPLETED.value,
    )


def test_list_backups(
    backup_service,
):
    service, repository, _ = backup_service

    repository.list_backups.return_value = [
        create_backup(
            id=1,
            name="backup1",
        ),
        create_backup(
            id=2,
            name="backup2",
        ),
    ]

    result = service.list_backups()

    assert len(result) == 2
    assert result[0]["name"] == "backup1"
    assert result[1]["name"] == "backup2"

    repository.list_backups.assert_called_once_with(
        status=None,
    )


def test_list_backups_with_filter(
    backup_service,
):
    service, repository, _ = backup_service

    repository.list_backups.return_value = []

    service.list_backups(
        BackupStatus.COMPLETED.value,
    )

    repository.list_backups.assert_called_once_with(
        status=BackupStatus.COMPLETED.value,
    )


def test_get_backup_info(
    backup_service,
):
    service, repository, _ = backup_service

    repository.list_backups.return_value = [
        create_backup(
            id=50,
        ),
    ]

    result = service.get_backup_info(
        50,
    )

    assert result["id"] == 50
    assert result["status"] == BackupStatus.COMPLETED.value


def test_get_backup_info_not_found(
    backup_service,
):
    service, repository, _ = backup_service

    repository.list_backups.return_value = []

    assert service.get_backup_info(
        999,
    ) is None




def test_verify_backup_success(
    backup_service,
    tmp_path,
):
    service, repository, _ = backup_service

    backup_dir = tmp_path / "backup"

    backup_dir.mkdir()

    file = backup_dir / "database.db"
    file.write_bytes(b"backup-data")

    checksum = hashlib.sha256(b"backup-data").hexdigest()

    repository.list_backups.return_value = [
        SimpleNamespace(
            id=1,
            file_path=str(backup_dir),
            checksum=checksum,
        )
    ]

    assert service.verify_backup(1) is True


def test_verify_backup_invalid_checksum(
    backup_service,
    tmp_path,
):
    service, repository, _ = backup_service

    backup_dir = tmp_path / "backup"

    backup_dir.mkdir()

    file = backup_dir / "database.db"
    file.write_bytes(b"backup-data")

    repository.list_backups.return_value = [
        SimpleNamespace(
            id=1,
            file_path=str(backup_dir),
            checksum="invalid-checksum",
        )
    ]

    assert service.verify_backup(1) is False


def test_verify_backup_not_found(
    backup_service,
):
    service, repository, _ = backup_service

    repository.list_backups.return_value = []

    assert service.verify_backup(999) is False


def test_verify_backup_directory_not_exists(
    backup_service,
):
    service, repository, _ = backup_service

    repository.list_backups.return_value = [
        SimpleNamespace(
            id=1,
            file_path="directory_that_does_not_exist",
            checksum="abc",
        )
    ]

    assert service.verify_backup(1) is False


def test_get_backup_info_without_dates(
    backup_service,
):
    service, repository, _ = backup_service

    backup = create_backup(
        id=10,
    )

    backup.created_at = None
    backup.completed_at = None

    repository.list_backups.return_value = [
        backup,
    ]

    result = service.get_backup_info(10)

    assert result["created_at"] is None
    assert result["completed_at"] is None


def test_list_backups_without_dates(
    backup_service,
):
    service, repository, _ = backup_service

    backup = create_backup()

    backup.created_at = None
    backup.completed_at = None

    repository.list_backups.return_value = [
        backup,
    ]

    result = service.list_backups()

    assert result[0]["created_at"] is None
    assert result[0]["completed_at"] is None


def test_create_manual_backup_database_missing(
    backup_service,
    tmp_path,
):
    service, repository, _ = backup_service

    service.database_path = str(tmp_path / "missing.db")

    backup = create_backup(
        id=200,
    )

    repository.create_backup.return_value = backup

    result = service.create_manual_backup(
        backup_dir=str(tmp_path),
    )

    assert result["backup_id"] == 200

    repository.create_backup.assert_called_once()

    repository.update_backup_status.assert_called_once_with(
        200,
        BackupStatus.COMPLETED.value,
    )


def test_create_manual_backup_repository_arguments(
    backup_service,
    tmp_path,
):
    service, repository, _ = backup_service

    backup = create_backup(
        id=300,
    )

    repository.create_backup.return_value = backup

    service.create_manual_backup(
        backup_dir=str(tmp_path),
        include_configs=False,
        include_logs=False,
    )

    _, kwargs = repository.create_backup.call_args

    assert kwargs["backup_type"] == "MANUAL"
    assert kwargs["config_included"] is False
    assert kwargs["logs_included"] is False
    assert "backup_" in kwargs["name"]
    assert kwargs["file_size_mb"] >= 0
    assert len(kwargs["checksum"]) == 64


def test_create_manual_backup_returns_expected_keys(
    backup_service,
    tmp_path,
):
    service, repository, _ = backup_service

    backup = create_backup(
        id=400,
    )

    repository.create_backup.return_value = backup

    result = service.create_manual_backup(
        backup_dir=str(tmp_path),
    )

    assert {
        "backup_id",
        "name",
        "path",
        "size_mb",
        "checksum",
        "timestamp",
    }.issubset(result.keys())


def test_verify_backup_multiple_files(
    backup_service,
    tmp_path,
):
    service, repository, _ = backup_service

    backup_dir = tmp_path / "backup"

    backup_dir.mkdir()

    file1 = backup_dir / "a.txt"
    file2 = backup_dir / "b.txt"

    file1.write_bytes(b"abc")
    file2.write_bytes(b"def")

    checksum = hashlib.sha256()
    checksum.update(b"abc")
    checksum.update(b"def")

    repository.list_backups.return_value = [
        SimpleNamespace(
            id=10,
            file_path=str(backup_dir),
            checksum=checksum.hexdigest(),
        )
    ]

    assert service.verify_backup(10) is True


def test_list_backups_empty(
    backup_service,
):
    service, repository, _ = backup_service

    repository.list_backups.return_value = []

    result = service.list_backups()

    assert result == []


def test_verify_backup_empty_directory(
    backup_service,
    tmp_path,
):
    service, repository, _ = backup_service

    backup_dir = tmp_path / "empty"

    backup_dir.mkdir()

    checksum = hashlib.sha256().hexdigest()

    repository.list_backups.return_value = [
        SimpleNamespace(
            id=30,
            file_path=str(backup_dir),
            checksum=checksum,
        )
    ]

    assert service.verify_backup(30) is True


def test_get_backup_info_returns_all_fields(
    backup_service,
):
    service, repository, _ = backup_service

    repository.list_backups.return_value = [
        create_backup(
            id=700,
            name="backup_final",
        )
    ]

    result = service.get_backup_info(
        700,
    )

    assert result["id"] == 700
    assert result["name"] == "backup_final"
    assert result["type"] == "MANUAL"
    assert result["status"] == BackupStatus.COMPLETED.value
    assert result["file_path"] == "backup_path"
    assert result["checksum"] == "checksum"