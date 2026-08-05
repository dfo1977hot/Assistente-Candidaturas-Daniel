"""Service for backup management."""

from datetime import datetime
import hashlib
import os
import shutil
from typing import Any

from sqlalchemy.orm import Session

from acd.database.local_state import resolve_database_path, user_data_directory
from acd.domain.platform.backup import BackupStatus
from acd.infrastructure.platform import StructuredLogger
from acd.infrastructure.repositories.platform import PlatformRepository


class BackupService:
    """Service for backup operations."""

    def __init__(self, session: Session, database_path: str = None) -> None:
        """Initialize service.

        Args:
            session: Database session
            database_path: Path to database file
        """
        self.session = session
        self.repository = PlatformRepository(session)
        self.logger = StructuredLogger(__name__)
        self.database_path = database_path or str(resolve_database_path())

    def create_manual_backup(
        self,
        backup_dir: str | None = None,
        include_configs: bool = True,
        include_logs: bool = True,
    ) -> dict[str, Any]:
        """Create manual backup.

        Args:
            backup_dir: Directory for backups
            include_configs: Include configuration files
            include_logs: Include logs

        Returns:
            Backup information
        """
        with self.logger.operation("create_manual_backup"):
            backup_dir = backup_dir or str(user_data_directory() / "backups")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
            backup_path = os.path.join(backup_dir, backup_name)

            # Create backup directory
            os.makedirs(backup_path, exist_ok=True)

            # Copy database
            db_backup = os.path.join(backup_path, "database.db")
            if os.path.exists(self.database_path):
                shutil.copy2(self.database_path, db_backup)

            # Calculate size and checksum
            total_size = 0
            checksum = hashlib.sha256()

            for root, _dirs, files in os.walk(backup_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    total_size += file_size

                    with open(file_path, "rb") as f:
                        checksum.update(f.read())

            # Create backup record
            backup = self.repository.create_backup(
                backup_type="MANUAL",
                name=backup_name,
                file_path=backup_path,
                file_size_mb=total_size / (1024 * 1024),
                checksum=checksum.hexdigest(),
                config_included=include_configs,
                logs_included=include_logs,
            )

            self.repository.update_backup_status(backup.id, BackupStatus.COMPLETED.value)

            return {
                "backup_id": backup.id,
                "name": backup_name,
                "path": backup_path,
                "size_mb": total_size / (1024 * 1024),
                "checksum": checksum.hexdigest(),
                "timestamp": datetime.now().isoformat(),
            }

    def list_backups(
        self,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """List backups.

        Args:
            status: Filter by status

        Returns:
            List of backups
        """
        backups = self.repository.list_backups(status=status)
        return [
            {
                "id": b.id,
                "name": b.name,
                "type": b.backup_type,
                "status": b.status,
                "size_mb": b.file_size_mb,
                "created_at": b.created_at.isoformat() if b.created_at else None,
                "completed_at": b.completed_at.isoformat() if b.completed_at else None,
            }
            for b in backups
        ]

    def verify_backup(self, backup_id: int) -> bool:
        """Verify backup integrity.

        Args:
            backup_id: Backup ID

        Returns:
            True if backup is valid
        """
        with self.logger.operation("verify_backup"):
            backups = self.repository.list_backups()
            backup = next((b for b in backups if b.id == backup_id), None)

            if not backup or not os.path.exists(backup.file_path):
                return False

            # Calculate checksum
            checksum = hashlib.sha256()
            for root, _dirs, files in os.walk(backup.file_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    with open(file_path, "rb") as f:
                        checksum.update(f.read())

            return checksum.hexdigest() == backup.checksum

    def get_backup_info(self, backup_id: int) -> dict[str, Any] | None:
        """Get backup information.

        Args:
            backup_id: Backup ID

        Returns:
            Backup information
        """
        backups = self.repository.list_backups()
        backup = next((b for b in backups if b.id == backup_id), None)

        if not backup:
            return None

        return {
            "id": backup.id,
            "name": backup.name,
            "type": backup.backup_type,
            "status": backup.status,
            "file_path": backup.file_path,
            "size_mb": backup.file_size_mb,
            "checksum": backup.checksum,
            "created_at": backup.created_at.isoformat() if backup.created_at else None,
            "completed_at": backup.completed_at.isoformat() if backup.completed_at else None,
        }
