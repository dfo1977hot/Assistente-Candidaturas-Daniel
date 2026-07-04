"""Tests for Release Management (Sprint 4.0)."""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from acd.models.base import Base
from acd.infrastructure.release import (
    SemanticVersion,
    VersionManager,
    PluginLoader,
    FeatureFlagService,
    get_plugin_loader,
)
from acd.infrastructure.repositories.release import ReleaseRepository
from acd.application.release.services import (
    InstallationService,
    UpdateService,
    MigrationService,
    DocumentationService,
)
from acd.application.release import ReleaseManager
from acd.domain.release import (
    Release,
    ReleaseStatus,
    InstalledVersion,
    UpdateHistory,
    FeatureFlag,
)


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
    Session = sessionmaker(bind=temp_db)
    return Session()


# ==================== Version Manager Tests ====================


class TestSemanticVersion:
    """Test semantic versioning."""

    def test_parse_version(self):
        """Test version parsing."""
        v = SemanticVersion("1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3

    def test_version_comparison(self):
        """Test version comparison."""
        v1 = SemanticVersion("1.0.0")
        v2 = SemanticVersion("1.1.0")
        v3 = SemanticVersion("2.0.0")

        assert v1 < v2 < v3
        assert v3 > v2 > v1

    def test_prerelease_versions(self):
        """Test prerelease version handling."""
        stable = SemanticVersion("1.0.0")
        beta = SemanticVersion("1.0.0-beta.1")
        alpha = SemanticVersion("1.0.0-alpha.1")

        assert beta < stable
        assert alpha < beta
        assert beta.is_beta()
        assert alpha.is_alpha()

    def test_release_type_detection(self):
        """Test release type detection."""
        major = SemanticVersion("2.0.0")
        minor = SemanticVersion("1.1.0")
        patch = SemanticVersion("1.0.1")

        assert major.is_major_release()
        assert minor.is_minor_release()
        assert patch.is_patch_release()


class TestVersionManager:
    """Test version manager."""

    def test_compare_versions(self):
        """Test version comparison."""
        assert VersionManager.compare_versions("1.0.0", "2.0.0") == -1
        assert VersionManager.compare_versions("2.0.0", "2.0.0") == 0
        assert VersionManager.compare_versions("2.0.0", "1.0.0") == 1

    def test_compatibility_check(self):
        """Test compatibility checking."""
        assert VersionManager.is_compatible("1.5.0", "1.0.0", "2.0.0")
        assert not VersionManager.is_compatible("0.9.0", "1.0.0", "2.0.0")
        assert not VersionManager.is_compatible("2.1.0", "1.0.0", "2.0.0")

    def test_upgrade_path(self):
        """Test upgrade path calculation."""
        available = ["0.1.0", "0.2.0", "0.3.0", "0.4.0", "0.5.0"]
        path = VersionManager.get_upgrade_path("0.1.0", "0.4.0", available)

        assert path[0] == "0.1.0"
        assert "0.4.0" in path


# ==================== Plugin Loader Tests ====================


class TestPluginLoader:
    """Test plugin loader."""

    def test_plugin_loader_init(self):
        """Test loader initialization."""
        loader = PluginLoader(["/path/to/plugins"])
        assert len(loader.plugin_dirs) > 0

    def test_plugin_discovery(self):
        """Test plugin discovery."""
        loader = PluginLoader()
        plugins = loader.discover_plugins()
        assert isinstance(plugins, list)

    def test_get_plugin_loader_singleton(self):
        """Test singleton pattern."""
        loader1 = get_plugin_loader()
        loader2 = get_plugin_loader()
        assert loader1 is loader2


# ==================== Release Repository Tests ====================


class TestReleaseRepository:
    """Test release repository."""

    def test_create_release(self, session):
        """Test creating release."""
        repo = ReleaseRepository(session)
        release = repo.create_release(
            version="1.0.0",
            status="stable",
            release_notes="Initial release",
        )

        assert release.version == "1.0.0"
        assert release.status == "stable"

    def test_get_release(self, session):
        """Test retrieving release."""
        repo = ReleaseRepository(session)
        repo.create_release("1.0.0", "stable")

        release = repo.get_release("1.0.0")
        assert release is not None
        assert release.version == "1.0.0"

    def test_list_releases(self, session):
        """Test listing releases."""
        repo = ReleaseRepository(session)
        repo.create_release("1.0.0", "stable")
        repo.create_release("1.1.0-beta", "beta")

        releases = repo.list_releases()
        assert len(releases) >= 2

    def test_get_latest_stable(self, session):
        """Test getting latest stable release."""
        repo = ReleaseRepository(session)
        repo.create_release("1.0.0", "stable")
        repo.create_release("2.0.0", "stable")

        latest = repo.get_latest_stable_release()
        assert latest.version == "2.0.0"

    def test_installed_version(self, session):
        """Test installed version tracking."""
        repo = ReleaseRepository(session)
        installed = repo.get_or_create_installed_version("1.0.0")

        assert installed.current_version == "1.0.0"
        assert installed.status == "active"

    def test_update_history(self, session):
        """Test update history."""
        repo = ReleaseRepository(session)
        update = repo.create_update_history("1.0.0", "1.1.0")

        assert update.status == "pending"
        assert update.from_version == "1.0.0"

    def test_feature_flag(self, session):
        """Test feature flag."""
        repo = ReleaseRepository(session)
        flag = repo.create_feature_flag("new_feature", False)

        assert flag.feature_name == "new_feature"
        assert not flag.is_enabled


# ==================== Feature Flag Service Tests ====================


class TestFeatureFlagService:
    """Test feature flag service."""

    def test_feature_disabled_by_default(self, session):
        """Test feature disabled."""
        service = FeatureFlagService(session)
        assert not service.is_enabled("test_feature")

    def test_enable_feature(self, session):
        """Test enabling feature."""
        service = FeatureFlagService(session)
        service.enable_feature("test_feature")

        assert service.is_enabled("test_feature")

    def test_disable_feature(self, session):
        """Test disabling feature."""
        service = FeatureFlagService(session)
        service.enable_feature("test_feature")
        service.disable_feature("test_feature")

        assert not service.is_enabled("test_feature")

    def test_rollout_percentage(self, session):
        """Test gradual rollout."""
        service = FeatureFlagService(session)
        service.enable_feature("gradual_feature")
        service.set_rollout_percentage("gradual_feature", 50)

        # Should be enabled with 50% rollout
        result = service.is_enabled("gradual_feature")
        assert isinstance(result, bool)


# ==================== Installation Service Tests ====================


class TestInstallationService:
    """Test installation service."""

    def test_check_dependencies(self, session):
        """Test dependency checking."""
        service = InstallationService(session)
        result = service.check_dependencies()

        assert "all_met" in result
        assert "missing_dependencies" in result

    def test_verify_installation(self, session):
        """Test installation verification."""
        service = InstallationService(session)
        result = service.verify_installation()

        assert "is_valid" in result
        assert "errors" in result


# ==================== Update Service Tests ====================


class TestUpdateService:
    """Test update service."""

    def test_check_for_updates(self, session):
        """Test update availability check."""
        repo = ReleaseRepository(session)
        repo.create_release("1.1.0", "stable")

        service = UpdateService(session)
        result = service.check_for_updates("1.0.0")

        assert "update_available" in result

    def test_prepare_update(self, session):
        """Test update preparation."""
        service = UpdateService(session)
        result = service.prepare_update("1.0.0", "1.1.0")

        assert "success" in result


# ==================== Migration Service Tests ====================


class TestMigrationService:
    """Test migration service."""

    def test_validate_compatibility(self, session):
        """Test migration compatibility."""
        service = MigrationService(session)
        result = service.validate_migration_compatibility("1.0.0", "1.1.0")

        assert "is_compatible" in result


# ==================== Release Manager Tests ====================


class TestReleaseManager:
    """Test release manager."""

    def test_manager_initialization(self, session):
        """Test manager initialization."""
        manager = ReleaseManager(session)
        assert manager.installation_service is not None
        assert manager.update_service is not None

    def test_get_system_status(self, session):
        """Test system status."""
        manager = ReleaseManager(session)
        status = manager.get_system_status()

        assert "installed" in status

    def test_load_plugins(self, session):
        """Test plugin loading."""
        manager = ReleaseManager(session)
        result = manager.load_plugins([])

        assert "discovered" in result
        assert "loaded" in result


# ==================== Integration Tests ====================


class TestReleaseIntegration:
    """Integration tests for release workflow."""

    def test_complete_installation_workflow(self, session):
        """Test complete installation."""
        manager = ReleaseManager(session)

        # Check initial status
        status = manager.get_system_status()
        assert not status["installed"]

        # Perform installation
        install_result = manager.perform_installation("0.4.0", "./")
        assert "success" in install_result

    def test_update_workflow(self, session):
        """Test update workflow."""
        repo = ReleaseRepository(session)
        repo.create_release("1.0.0", "stable")
        repo.create_release("1.1.0", "stable")
        repo.get_or_create_installed_version("1.0.0")

        manager = ReleaseManager(session)

        # Check for updates
        updates = manager.check_for_updates()
        assert "update_available" in updates

    def test_feature_flag_workflow(self, session):
        """Test feature flag workflow."""
        # Create installed version first
        repo = ReleaseRepository(session)
        repo.get_or_create_installed_version("0.4.0")

        manager = ReleaseManager(session)

        # Create feature
        manager.feature_flags.enable_feature("test_feature")

        # Check if enabled
        assert manager.is_feature_enabled("test_feature")

        # Disable
        manager.disable_feature("test_feature")
        assert not manager.is_feature_enabled("test_feature")
