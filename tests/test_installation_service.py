"""Tests for InstallationService."""

from unittest.mock import MagicMock, patch

import pytest

from acd.application.release.services.installation_service import (
    InstallationService,
)


@pytest.fixture
def installation_service():
    """Create InstallationService with mocked dependencies."""

    session = MagicMock()

    with (
        patch(
            "acd.application.release.services.installation_service.ReleaseRepository"
        ) as repository_cls,
        patch(
            "acd.application.release.services.installation_service.StructuredLogger"
        ) as logger_cls,
    ):
        repository = MagicMock()
        logger = MagicMock()

        repository_cls.return_value = repository
        logger_cls.return_value = logger

        service = InstallationService(
            session=session,
            installation_path="./test_installation",
        )

        yield (
            service,
            session,
            repository,
            logger,
        )


def test_get_installation_info_not_installed(
    installation_service,
):
    """Return information when no installation exists."""

    (
        service,
        _session,
        repository,
        _logger,
    ) = installation_service

    repository.get_installed_version.return_value = None

    result = service.get_installation_info()

    assert result == {
        "installed": False,
        "version": None,
        "installation_path": None,
    }


def test_get_installation_info(
    installation_service,
):
    """Return information for an installed version."""

    (
        service,
        _session,
        repository,
        _logger,
    ) = installation_service

    installed = MagicMock()
    installed.current_version = "2.0.0"
    installed.installation_path = "./acd"
    installed.installation_date.isoformat.return_value = (
        "2026-01-01T00:00:00+00:00"
    )
    installed.status = "ACTIVE"
    installed.is_beta = False

    repository.get_installed_version.return_value = installed

    result = service.get_installation_info()

    assert result == {
        "installed": True,
        "version": "2.0.0",
        "installation_path": "./acd",
        "installation_date": "2026-01-01T00:00:00+00:00",
        "status": "ACTIVE",
        "is_beta": False,
    }


def test_perform_fresh_install_success(
    installation_service,
    tmp_path,
):
    """Successful fresh installation."""

    (
        service,
        session,
        repository,
        logger,
    ) = installation_service

    log_entry = MagicMock()
    log_entry.id = 100

    installed = MagicMock()
    installed.id = 55

    repository.create_installation_log.return_value = log_entry
    repository.get_or_create_installed_version.return_value = installed

    logger.operation.return_value.__enter__.return_value = None
    logger.operation.return_value.__exit__.return_value = None

    install_path = tmp_path / "acd"

    with patch(
        "acd.application.release.services.installation_service.VersionManager.parse_version"
    ) as parse_version:
        parse_version.return_value = (1, 0, 0)

        result = service.perform_fresh_install(
            app_version="1.0.0",
            installation_path=str(install_path),
            include_default_configs=True,
        )

    assert result["success"] is True
    assert result["installation_id"] == 55

    assert install_path.exists()
    assert (install_path / "config").exists()
    assert (install_path / "backups").exists()
    assert (install_path / "logs").exists()
    assert (install_path / "data").exists()

    repository.create_installation_log.assert_called_once()
    repository.update_installation_log.assert_called_once()
    repository.get_or_create_installed_version.assert_called_once_with("1.0.0")

    session.commit.assert_called_once()

    logger.info.assert_called_once()


def test_perform_fresh_install_invalid_version(
    installation_service,
):
    """Invalid version should return failure and update installation log."""

    (
        service,
        session,
        repository,
        logger,
    ) = installation_service

    log_entry = MagicMock()
    log_entry.id = 200

    repository.create_installation_log.return_value = log_entry

    logger.operation.return_value.__enter__.return_value = None
    logger.operation.return_value.__exit__.return_value = None

    with patch(
        "acd.application.release.services.installation_service.VersionManager.parse_version"
    ) as parse_version:
        parse_version.side_effect = ValueError("invalid version")

        result = service.perform_fresh_install(
            app_version="abc",
            installation_path="./temp",
        )

    assert result["success"] is False
    assert "Invalid version format" in result["message"]
    assert result["installation_id"] is None

    repository.create_installation_log.assert_called_once()

    repository.update_installation_log.assert_called_once_with(
        200,
        status="FAILED",
        duration_seconds=result["duration_seconds"],
        error_message="Invalid version format: abc",
    )

    session.commit.assert_not_called()

    logger.error.assert_called_once()


def test_check_dependencies_all_met(
    installation_service,
):
    """All required packages are available."""

    (
        service,
        _session,
        _repository,
        _logger,
    ) = installation_service

    with patch(
        "importlib.import_module"
    ) as import_module:
        import_module.return_value = MagicMock()

        result = service.check_dependencies()

    assert result["all_met"] is True
    assert result["missing_dependencies"] == []

    assert "os" in result["system_info"]
    assert "python_version" in result["system_info"]
    assert "python_executable" in result["system_info"]

    assert import_module.call_count == 4


def test_check_dependencies_missing_packages(
    installation_service,
):
    """Some required packages are missing."""

    (
        service,
        _session,
        _repository,
        _logger,
    ) = installation_service

    def side_effect(package):
        if package in {"pyside6", "requests"}:
            raise ImportError(package)
        return MagicMock()

    with patch(
        "importlib.import_module",
        side_effect=side_effect,
    ):
        result = service.check_dependencies()

    assert result["all_met"] is False
    assert result["missing_dependencies"] == [
        "pyside6",
        "requests",
    ]


def test_verify_installation_success(
    installation_service,
    tmp_path,
):
    """Installation is valid."""

    (
        service,
        _session,
        repository,
        _logger,
    ) = installation_service

    install_path = tmp_path / "acd"
    install_path.mkdir()

    for directory in (
        "config",
        "backups",
        "logs",
        "data",
    ):
        (install_path / directory).mkdir()

    service.installation_path = install_path

    repository.get_installed_version.return_value = MagicMock()

    with patch.object(
        service,
        "check_dependencies",
        return_value={
            "all_met": True,
            "missing_dependencies": [],
            "system_info": {},
        },
    ):
        result = service.verify_installation()

    assert result["is_valid"] is True
    assert result["errors"] == []
    assert result["warnings"] == []


def test_verify_installation_missing_directories(
    installation_service,
    tmp_path,
):
    """Missing optional directories should generate warnings only."""

    (
        service,
        _session,
        repository,
        _logger,
    ) = installation_service

    install_path = tmp_path / "acd"
    install_path.mkdir()

    service.installation_path = install_path

    repository.get_installed_version.return_value = MagicMock()

    with patch.object(
        service,
        "check_dependencies",
        return_value={
            "all_met": True,
            "missing_dependencies": [],
            "system_info": {},
        },
    ):
        result = service.verify_installation()

    assert result["is_valid"] is True
    assert result["errors"] == []
    assert len(result["warnings"]) == 4


def test_verify_installation_invalid(
    installation_service,
    tmp_path,
):
    """Missing installation record and dependencies."""

    (
        service,
        _session,
        repository,
        _logger,
    ) = installation_service

    install_path = tmp_path / "acd"
    install_path.mkdir()

    service.installation_path = install_path

    repository.get_installed_version.return_value = None

    with patch.object(
        service,
        "check_dependencies",
        return_value={
            "all_met": False,
            "missing_dependencies": ["sqlalchemy"],
            "system_info": {},
        },
    ):
        result = service.verify_installation()

    assert result["is_valid"] is False
    print(result)

    assert "No installed version record found" in result["errors"]

    assert "Missing: sqlalchemy" in result["errors"]


def test_perform_fresh_install_without_default_configs(
    installation_service,
    tmp_path,
):
    """Fresh install without default config directories."""

    service, session, repository, logger = installation_service

    log_entry = MagicMock()
    log_entry.id = 300

    installed = MagicMock()
    installed.id = 88

    repository.create_installation_log.return_value = log_entry
    repository.get_or_create_installed_version.return_value = installed

    logger.operation.return_value.__enter__.return_value = None
    logger.operation.return_value.__exit__.return_value = None

    install_path = tmp_path / "acd"

    result = service.perform_fresh_install(
        app_version="1.0.0",
        installation_path=str(install_path),
        include_default_configs=False,
    )

    assert result["success"] is True
    assert install_path.exists()
    assert not (install_path / "config").exists()
    assert not (install_path / "backups").exists()
    assert not (install_path / "logs").exists()
    assert not (install_path / "data").exists()

    repository.update_installation_log.assert_called_once_with(
        300,
        status="SUCCESS",
        duration_seconds=result["duration_seconds"],
    )

    session.commit.assert_called_once()
    logger.info.assert_called_once()


def test_perform_fresh_install_log_creation_failure(
    installation_service,
):
    """Failure before log entry exists."""

    service, session, repository, logger = installation_service

    repository.create_installation_log.side_effect = RuntimeError(
        "log failed",
    )

    result = service.perform_fresh_install(
        app_version="1.0.0",
        installation_path="./temp",
    )

    assert result["success"] is False
    assert "log failed" in result["message"]
    assert result["installation_id"] is None

    repository.update_installation_log.assert_not_called()
    session.commit.assert_not_called()
    logger.error.assert_called_once()


def test_verify_installation_missing_installation_directory(
    installation_service,
    tmp_path,
):
    """Missing installation directory should be reported as error."""

    service, _session, repository, _logger = installation_service

    service.installation_path = tmp_path / "missing_installation"

    repository.get_installed_version.return_value = MagicMock()

    with patch.object(
        service,
        "check_dependencies",
        return_value={
            "all_met": True,
            "missing_dependencies": [],
            "system_info": {},
        },
    ):
        result = service.verify_installation()

    assert result["is_valid"] is False
    assert any(
        "installation directory not found" in error.lower()
        for error in result["errors"]
    )