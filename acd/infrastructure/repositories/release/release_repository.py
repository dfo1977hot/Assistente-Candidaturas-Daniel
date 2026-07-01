"""Release repository for data access."""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from acd.domain.release import (
    Release,
    InstalledVersion,
    UpdateHistory,
    InstallationLog,
    MigrationHistory,
    FeatureFlag,
    DocumentationTopic,
)


class ReleaseRepository:
    """Repository for release management data access."""

    def __init__(self, session: Session):
        """Initialize repository.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    # ==================== Release Methods ====================

    def create_release(
        self,
        version: str,
        status: str,
        release_notes: str = "",
        download_url: str | None = None,
        file_size_mb: float = 0.0,
        is_critical: bool = False,
    ) -> Release:
        """Create a new release."""
        release = Release(
            version=version,
            status=status,
            release_notes=release_notes,
            download_url=download_url,
            file_size_mb=file_size_mb,
            is_critical=is_critical,
        )
        self.session.add(release)
        self.session.commit()
        return release

    def get_release(self, version: str) -> Release | None:
        """Get release by version."""
        return self.session.query(Release).filter_by(version=version).first()

    def list_releases(
        self,
        status: str | None = None,
        is_beta: bool | None = None,
        limit: int = 100,
    ) -> list[Release]:
        """List releases with optional filtering."""
        query = self.session.query(Release)

        if status:
            query = query.filter_by(status=status)

        if is_beta is not None:
            query = query.filter_by(status="beta" if is_beta else "stable")

        return query.order_by(desc(Release.release_date)).limit(limit).all()

    def get_latest_stable_release(self) -> Release | None:
        """Get latest stable release."""
        return (
            self.session.query(Release)
            .filter_by(status="stable")
            .order_by(desc(Release.release_date))
            .first()
        )

    def get_latest_beta_release(self) -> Release | None:
        """Get latest beta release."""
        return (
            self.session.query(Release)
            .filter_by(status="beta")
            .order_by(desc(Release.release_date))
            .first()
        )

    def update_release_status(self, version: str, status: str) -> bool:
        """Update release status."""
        release = self.get_release(version)
        if not release:
            return False

        release.status = status
        self.session.commit()
        return True

    # ==================== Installed Version Methods ====================

    def get_or_create_installed_version(self, current_version: str) -> InstalledVersion:
        """Get or create installed version record."""
        installed = self.session.query(InstalledVersion).filter_by(status="active").first()

        if installed:
            return installed

        installed = InstalledVersion(
            current_version=current_version,
            installation_path="./",
            installation_type="fresh_install",
            status="active",
        )
        self.session.add(installed)
        self.session.commit()
        return installed

    def update_installed_version(
        self,
        current_version: str,
        new_version: str,
        installation_type: str = "upgraded",
    ) -> bool:
        """Update installed version after upgrade."""
        installed = self.session.query(InstalledVersion).filter_by(status="active").first()

        if not installed:
            return False

        installed.previous_version = current_version
        installed.current_version = new_version
        installed.installation_type = installation_type
        installed.last_update_date = datetime.now()
        self.session.commit()
        return True

    def get_installed_version(self) -> InstalledVersion | None:
        """Get current installed version."""
        return self.session.query(InstalledVersion).filter_by(status="active").first()

    # ==================== Update History Methods ====================

    def create_update_history(
        self,
        from_version: str,
        to_version: str,
        update_type: str = "patch",
        is_automatic: bool = False,
    ) -> UpdateHistory:
        """Create update history entry."""
        update = UpdateHistory(
            from_version=from_version,
            to_version=to_version,
            update_type=update_type,
            status="pending",
            is_automatic=is_automatic,
        )
        self.session.add(update)
        self.session.commit()
        return update

    def update_history_status(
        self,
        update_id: int,
        status: str,
        duration_minutes: int = 0,
        error_message: str | None = None,
    ) -> bool:
        """Update update history status."""
        update = self.session.query(UpdateHistory).filter_by(id=update_id).first()

        if not update:
            return False

        update.status = status
        update.completion_date = datetime.now()
        update.duration_minutes = duration_minutes
        if error_message:
            update.error_message = error_message

        self.session.commit()
        return True

    def list_update_history(
        self,
        status: str | None = None,
        limit: int = 50,
    ) -> list[UpdateHistory]:
        """List update history."""
        query = self.session.query(UpdateHistory)

        if status:
            query = query.filter_by(status=status)

        return query.order_by(desc(UpdateHistory.update_date)).limit(limit).all()

    def get_last_successful_update(self) -> UpdateHistory | None:
        """Get last successful update."""
        return (
            self.session.query(UpdateHistory)
            .filter_by(status="completed")
            .order_by(desc(UpdateHistory.update_date))
            .first()
        )

    # ==================== Installation Log Methods ====================

    def create_installation_log(
        self,
        operation: str,
        status: str,
        message: str,
        details: dict | None = None,
    ) -> InstallationLog:
        """Create installation log entry."""
        log = InstallationLog(
            operation=operation,
            status=status,
            message=message,
            details=details or {},
        )
        self.session.add(log)
        self.session.commit()
        return log

    def update_installation_log(
        self,
        log_id: int,
        status: str,
        duration_seconds: int = 0,
        error_message: str | None = None,
    ) -> bool:
        """Update installation log."""
        log = self.session.query(InstallationLog).filter_by(id=log_id).first()

        if not log:
            return False

        log.status = status
        log.end_time = datetime.now()
        log.duration_seconds = duration_seconds
        if error_message:
            log.error_message = error_message

        self.session.commit()
        return True

    def list_installation_logs(
        self,
        operation: str | None = None,
        hours_back: int = 24,
        limit: int = 100,
    ) -> list[InstallationLog]:
        """List installation logs."""
        query = self.session.query(InstallationLog)

        if operation:
            query = query.filter_by(operation=operation)

        cutoff = datetime.now() - timedelta(hours=hours_back)
        query = query.filter(InstallationLog.start_time >= cutoff)

        return query.order_by(desc(InstallationLog.start_time)).limit(limit).all()

    # ==================== Migration History Methods ====================

    def create_migration_history(
        self,
        migration_name: str,
        source_version: str,
        target_version: str,
        migration_type: str = "database",
    ) -> MigrationHistory:
        """Create migration history entry."""
        migration = MigrationHistory(
            migration_name=migration_name,
            source_version=source_version,
            target_version=target_version,
            migration_type=migration_type,
            status="pending",
        )
        self.session.add(migration)
        self.session.commit()
        return migration

    def update_migration_status(
        self,
        migration_id: int,
        status: str,
        records_migrated: int = 0,
        records_failed: int = 0,
        duration_seconds: int = 0,
    ) -> bool:
        """Update migration status."""
        migration = self.session.query(MigrationHistory).filter_by(id=migration_id).first()

        if not migration:
            return False

        migration.status = status
        migration.completion_date = datetime.now()
        migration.records_migrated = records_migrated
        migration.records_failed = records_failed
        migration.duration_seconds = duration_seconds

        self.session.commit()
        return True

    def list_migration_history(
        self,
        status: str | None = None,
        limit: int = 50,
    ) -> list[MigrationHistory]:
        """List migration history."""
        query = self.session.query(MigrationHistory)

        if status:
            query = query.filter_by(status=status)

        return query.order_by(desc(MigrationHistory.migration_date)).limit(limit).all()

    # ==================== Feature Flag Methods ====================

    def get_feature_flag(self, feature_name: str) -> FeatureFlag | None:
        """Get feature flag by name."""
        return self.session.query(FeatureFlag).filter_by(feature_name=feature_name).first()

    def list_feature_flags(self) -> list[FeatureFlag]:
        """List all feature flags."""
        return self.session.query(FeatureFlag).all()

    def create_feature_flag(
        self,
        feature_name: str,
        is_enabled: bool = False,
        description: str = "",
    ) -> FeatureFlag:
        """Create feature flag."""
        flag = FeatureFlag(
            feature_name=feature_name,
            is_enabled=is_enabled,
            description=description,
        )
        self.session.add(flag)
        self.session.commit()
        return flag

    # ==================== Documentation Methods ====================

    def get_documentation_topic(self, topic_id: str) -> DocumentationTopic | None:
        """Get documentation topic by ID."""
        return self.session.query(DocumentationTopic).filter_by(topic_id=topic_id).first()

    def list_documentation_topics(
        self,
        category: str | None = None,
        is_featured: bool | None = None,
        limit: int = 100,
    ) -> list[DocumentationTopic]:
        """List documentation topics."""
        query = self.session.query(DocumentationTopic).filter_by(is_visible=True)

        if category:
            query = query.filter_by(category=category)

        if is_featured is not None:
            query = query.filter_by(is_featured=is_featured)

        return query.order_by(desc(DocumentationTopic.view_count)).limit(limit).all()

    def search_documentation(
        self,
        search_query: str,
        limit: int = 20,
    ) -> list[DocumentationTopic]:
        """Search documentation topics."""
        query_lower = search_query.lower()
        topics = self.session.query(DocumentationTopic).filter_by(is_visible=True).all()

        results = [t for t in topics if t.matches_search(search_query)]
        return results[:limit]

    def update_documentation_view_count(self, topic_id: str) -> bool:
        """Update documentation view count."""
        topic = self.get_documentation_topic(topic_id)
        if not topic:
            return False

        topic.view_count += 1
        topic.last_viewed = datetime.now()
        self.session.commit()
        return True
