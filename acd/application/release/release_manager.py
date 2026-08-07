"""Release manager for coordinating release operations."""

from acd.application.release.services import (
    DocumentationService,
    InstallationService,
    MigrationService,
    UpdateService,
)
from acd.infrastructure.platform import StructuredLogger
from acd.infrastructure.release import (
    FeatureFlagService,
    VersionManager,
    get_plugin_loader,
)
from acd.infrastructure.repositories.release import ReleaseRepository
from acd.version import get_version


class ReleaseManager:
    """Orchestrate all release operations."""

    def __init__(self, session, database_path: str | None = None):
        """Initialize release manager.

        Args:
            session: SQLAlchemy database session
            database_path: Path to database for backups
        """
        self.session = session
        self.database_path = database_path
        self.logger = StructuredLogger("ReleaseManager")

        # Initialize services
        self.repository = ReleaseRepository(session)
        self.installation_service = InstallationService(session, "./")
        self.update_service = UpdateService(session, database_path)
        self.migration_service = MigrationService(session)
        self.documentation_service = DocumentationService(session)
        self.feature_flags = FeatureFlagService(session)

        # Plugin loader
        self.plugin_loader = get_plugin_loader()

    def get_system_status(self) -> dict:
        """Get comprehensive system release status."""
        try:
            installed = self.repository.get_installed_version()
            latest_stable = self.repository.get_latest_stable_release()
            latest_beta = self.repository.get_latest_beta_release()

            if not installed:
                return {
                    "installed": False,
                    "version": None,
                    "status": "not_installed",
                }

            updates_available = False
            latest_available_version = None

            if (
                latest_stable
                and VersionManager.compare_versions(
                    installed.current_version,
                    latest_stable.version,
                )
                < 0
            ):
                updates_available = True
                latest_available_version = latest_stable.version

            return {
                "installed": True,
                "current_version": installed.current_version,
                "installation_path": installed.installation_path,
                "installation_date": installed.installation_date.isoformat(),
                "status": installed.status,
                "is_beta": installed.is_beta,
                "updates_available": updates_available,
                "latest_available_version": latest_available_version,
                "latest_stable": latest_stable.version if latest_stable else None,
                "latest_beta": latest_beta.version if latest_beta else None,
                "features": self.feature_flags.get_all_flags(installed.current_version),
            }

        except Exception as e:
            self.logger.error(
                "get_system_status_failed",
                f"Failed to get system status: {str(e)}",
                error_type=type(e).__name__,
            )
            return {"installed": False, "error": str(e)}

    def perform_installation(
        self,
        app_version: str,
        installation_path: str,
        include_defaults: bool = True,
    ) -> dict:
        """Perform full installation."""
        with self.logger.operation(f"install_v{app_version}"):
            result = self.installation_service.perform_fresh_install(
                app_version,
                installation_path,
                include_defaults,
            )

            if result["success"]:
                self.logger.info(
                    "installation_completed",
                    f"Installation completed: {result['message']}",
                )

            return result

    def perform_update(
        self,
        from_version: str,
        to_version: str,
    ) -> dict:
        """Perform full update with migration."""
        try:
            with self.logger.operation(f"update_v{from_version}_to_v{to_version}"):
                # 1. Prepare update
                prep_result = self.update_service.prepare_update(
                    from_version,
                    to_version,
                )

                if not prep_result["success"]:
                    return prep_result

                update_id = prep_result["update_id"]

                # 2. Perform migration
                migration_result = self.migration_service.create_migration(
                    from_version,
                    to_version,
                    migration_type="database",
                )

                if not migration_result["success"]:
                    self.update_service.fail_update(
                        update_id,
                        migration_result["message"],
                    )
                    return migration_result

                # 3. Complete update
                duration_minutes = 5  # Placeholder
                self.update_service.complete_update(
                    update_id,
                    from_version,
                    to_version,
                    duration_minutes,
                )

                # Update installed version
                self.repository.update_installed_version(
                    from_version,
                    to_version,
                    installation_type="upgraded",
                )

                self.logger.info(
                    "update_completed",
                    f"Update completed: {from_version} → {to_version}",
                )

                return {
                    "success": True,
                    "message": f"Update completed: {from_version} → {to_version}",
                    "update_id": update_id,
                    "backup_path": prep_result.get("backup_path"),
                }

        except Exception as e:
            self.logger.error(
                "update_failed",
                f"Update failed: {str(e)}",
                error_type=type(e).__name__,
            )
            return {
                "success": False,
                "message": f"Update failed: {str(e)}",
            }

    def check_for_updates(self, include_beta: bool = False) -> dict:
        """Check for available updates."""
        installed = self.repository.get_installed_version()
        if not installed:
            return {"update_available": False}

        return self.update_service.check_for_updates(
            installed.current_version,
            include_beta,
        )

    def rollback_to_previous(self) -> dict:
        """Rollback to previous version."""
        last_update = self.repository.get_last_successful_update()
        if not last_update or not last_update.can_rollback():
            return {
                "success": False,
                "message": "No rollback available",
            }

        return self.update_service.rollback_update(last_update.id, last_update.from_version)

    def enable_feature(self, feature_name: str) -> bool:
        """Enable a feature flag."""
        return self.feature_flags.enable_feature(feature_name)

    def disable_feature(self, feature_name: str) -> bool:
        """Disable a feature flag."""
        return self.feature_flags.disable_feature(feature_name)

    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if feature is enabled."""
        installed = self.repository.get_installed_version()
        if not installed:
            return False

        return self.feature_flags.is_enabled(
            feature_name,
            installed.current_version,
        )

    def load_plugins(self, plugin_dirs: list[str] | None = None) -> dict:
        """Load available plugins."""
        if plugin_dirs:
            for dir_path in plugin_dirs:
                self.plugin_loader.add_plugin_dir(dir_path)

        # Set context for plugins
        installed = self.repository.get_installed_version()
        context = {
            "app_version": installed.current_version if installed else get_version(),
        }
        self.plugin_loader.set_context(context)

        # Discover and load plugins
        plugins = self.plugin_loader.discover_plugins()
        loaded = []

        for plugin_name in plugins:
            if self.plugin_loader.load_plugin(plugin_name):
                loaded.append(plugin_name)

        return {
            "discovered": len(plugins),
            "loaded": len(loaded),
            "plugins": loaded,
        }

    def get_release_notes(self, version: str) -> str:
        """Get release notes for a version."""
        release = self.repository.get_release(version)
        if not release:
            return ""
        return release.release_notes

    def search_help(self, query: str) -> list[dict]:
        """Search help documentation."""
        return self.documentation_service.search_documentation(query)

    def get_help_topic(self, topic_id: str) -> dict | None:
        """Get help topic."""
        return self.documentation_service.get_topic(topic_id)

    def get_system_overview(self) -> dict:
        """Get complete system overview."""
        return {
            "status": self.get_system_status(),
            "installation_info": self.installation_service.get_installation_info(),
            "dependencies": self.installation_service.check_dependencies(),
            "verification": self.installation_service.verify_installation(),
            "update_history": self.update_service.get_update_history(limit=10),
            "rollback_options": self.update_service.get_rollback_options(),
            "migration_history": self.migration_service.get_migration_history(limit=10),
            "featured_topics": self.documentation_service.get_featured_topics(),
        }
