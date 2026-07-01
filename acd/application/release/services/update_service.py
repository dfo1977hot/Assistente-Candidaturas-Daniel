"""Update service for application updates."""

from datetime import datetime
from pathlib import Path
import shutil
import hashlib

from acd.infrastructure.platform import StructuredLogger
from acd.infrastructure.repositories.release import ReleaseRepository
from acd.infrastructure.release import VersionManager


class UpdateService:
    """Handle application updates and versioning."""

    def __init__(self, session, database_path: str | None = None):
        """Initialize update service.
        
        Args:
            session: SQLAlchemy database session
            database_path: Path to database for backup during update
        """
        self.session = session
        self.database_path = database_path
        self.repository = ReleaseRepository(session)
        self.logger = StructuredLogger("UpdateService")

    def check_for_updates(
        self,
        current_version: str,
        include_beta: bool = False,
    ) -> dict:
        """Check if updates are available.
        
        Returns:
            {
                "update_available": bool,
                "current_version": str,
                "latest_version": str | None,
                "latest_release": dict | None,
                "is_critical": bool,
            }
        """
        try:
            current = VersionManager.parse_version(current_version)

            # Get latest stable release
            latest_stable = self.repository.get_latest_stable_release()

            if include_beta:
                latest_beta = self.repository.get_latest_beta_release()
                latest = latest_beta if (latest_beta and latest_beta.version > (latest_stable.version if latest_stable else "0.0.0")) else latest_stable
            else:
                latest = latest_stable

            if not latest:
                return {
                    "update_available": False,
                    "current_version": current_version,
                    "latest_version": None,
                    "latest_release": None,
                    "is_critical": False,
                }

            latest_parsed = VersionManager.parse_version(latest.version)

            if latest_parsed > current:
                return {
                    "update_available": True,
                    "current_version": current_version,
                    "latest_version": latest.version,
                    "latest_release": latest.to_dict(),
                    "is_critical": latest.is_critical,
                }
            else:
                return {
                    "update_available": False,
                    "current_version": current_version,
                    "latest_version": None,
                    "latest_release": None,
                    "is_critical": False,
                }

        except Exception as e:
            self.logger.error(
                "check_for_updates_failed",
                f"Failed to check for updates: {str(e)}",
                error_type=type(e).__name__,
            )
            return {
                "update_available": False,
                "current_version": current_version,
                "latest_version": None,
                "latest_release": None,
                "is_critical": False,
            }

    def prepare_update(
        self,
        from_version: str,
        to_version: str,
        update_package_path: str | None = None,
    ) -> dict:
        """Prepare for update by creating backup and logs.
        
        Returns:
            {
                "success": bool,
                "update_id": int | None,
                "backup_path": str | None,
                "message": str,
            }
        """
        try:
            with self.logger.operation("prepare_update"):
                # Verify versions
                VersionManager.parse_version(from_version)
                VersionManager.parse_version(to_version)

                # Create backup if database path provided
                backup_path = None
                if self.database_path:
                    backup_dir = Path("./backups")
                    backup_dir.mkdir(exist_ok=True)

                    db_path = Path(self.database_path)
                    if db_path.exists():
                        backup_file = (
                            backup_dir
                            / f"db_backup_{from_version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                        )
                        shutil.copy2(db_path, backup_file)
                        backup_path = str(backup_file.absolute())

                # Determine update type
                from_parsed = VersionManager.parse_version(from_version)
                to_parsed = VersionManager.parse_version(to_version)

                if from_parsed.major != to_parsed.major:
                    update_type = "MAJOR"
                elif from_parsed.minor != to_parsed.minor:
                    update_type = "MINOR"
                else:
                    update_type = "PATCH"

                # Create update history
                update = self.repository.create_update_history(
                    from_version=from_version,
                    to_version=to_version,
                    update_type=update_type,
                    is_automatic=False,
                )

                self.logger.info(
                    "update_prepared",
                    f"Update prepared from {from_version} to {to_version}",
                    duration_ms=0,
                    result="success",
                )

                return {
                    "success": True,
                    "update_id": update.id,
                    "backup_path": backup_path,
                    "message": f"Update prepared: {from_version} → {to_version}",
                }

        except Exception as e:
            self.logger.error(
                "prepare_update_failed",
                f"Failed to prepare update: {str(e)}",
                error_type=type(e).__name__,
            )

            return {
                "success": False,
                "update_id": None,
                "backup_path": None,
                "message": f"Update preparation failed: {str(e)}",
            }

    def complete_update(
        self,
        update_id: int,
        from_version: str,
        to_version: str,
        duration_minutes: int,
    ) -> bool:
        """Mark update as completed."""
        return self.repository.update_history_status(
            update_id,
            status="completed",
            duration_minutes=duration_minutes,
        )

    def fail_update(
        self,
        update_id: int,
        error_message: str,
        duration_minutes: int = 0,
    ) -> bool:
        """Mark update as failed."""
        return self.repository.update_history_status(
            update_id,
            status="failed",
            duration_minutes=duration_minutes,
            error_message=error_message,
        )

    def rollback_update(self, update_id: int, from_version: str) -> dict:
        """Rollback to previous version.
        
        Returns:
            {
                "success": bool,
                "message": str,
                "rolled_back_to": str | None,
            }
        """
        try:
            with self.logger.operation("rollback_update"):
                update = self.session.query(UpdateHistory).filter_by(id=update_id).first()

                if not update:
                    return {
                        "success": False,
                        "message": "Update record not found",
                        "rolled_back_to": None,
                    }

                if update.status != "completed":
                    return {
                        "success": False,
                        "message": "Can only rollback completed updates",
                        "rolled_back_to": None,
                    }

                if not update.rollback_available:
                    return {
                        "success": False,
                        "message": "Rollback not available for this update",
                        "rolled_back_to": None,
                    }

                # Mark as rolled back
                update.status = "rolled_back"
                self.session.commit()

                self.logger.info(
                    "update_rolled_back",
                    f"Update rolled back from {update.to_version} to {update.from_version}",
                )

                return {
                    "success": True,
                    "message": f"Rolled back to {update.from_version}",
                    "rolled_back_to": update.from_version,
                }

        except Exception as e:
            self.logger.error(
                "rollback_failed",
                f"Rollback failed: {str(e)}",
                error_type=type(e).__name__,
            )

            return {
                "success": False,
                "message": f"Rollback failed: {str(e)}",
                "rolled_back_to": None,
            }

    def get_update_history(self, limit: int = 20) -> list[dict]:
        """Get update history."""
        updates = self.repository.list_update_history(limit=limit)
        return [u.to_dict() for u in updates]

    def get_rollback_options(self) -> list[dict]:
        """Get available rollback options."""
        updates = self.repository.list_update_history(
            status="completed",
            limit=10,
        )

        return [
            {
                "update_id": u.id,
                "from_version": u.from_version,
                "to_version": u.to_version,
                "update_date": u.update_date.isoformat(),
                "can_rollback": u.can_rollback(),
            }
            for u in updates
            if u.can_rollback()
        ]


# Import UpdateHistory from domain
from acd.domain.release import UpdateHistory
