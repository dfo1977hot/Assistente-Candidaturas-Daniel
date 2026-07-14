"""Service for backup restoration."""

from datetime import datetime
import hashlib
import os
import shutil
from typing import Any

from sqlalchemy.orm import Session

from acd.domain.platform.backup import BackupStatus
from acd.infrastructure.platform import StructuredLogger
from acd.infrastructure.repositories.platform import PlatformRepository


class RestoreService:
    """Service for restore operations."""

    def __init__(self, session: Session, database_path: str = None) -> None:
        """Initialize service.

        Args:
            session: Database session
            database_path: Path to database file
        """
        self.session = session
        self.repository = PlatformRepository(session)
        self.logger = StructuredLogger(__name__)
        self.database_path = database_path or "acd.db"

    def restore_from_backup(
        self,
        backup_id: int,
        verify: bool = True,
    ) -> dict[str, Any]:
        """Restore from backup.

        Args:
            backup_id: Backup ID to restore
            verify: Verify backup before restore

        Returns:
            Restore information
        """
        with self.logger.operation("restore_from_backup"):
            # Get backup
            backups = self.repository.list_backups()
            backup = next((b for b in backups if b.id == backup_id), None)

            if not backup:
                raise ValueError(f"Backup {backup_id} not found")

            # Verify backup
            if verify and not self._verify_backup(backup):
                raise ValueError(f"Backup {backup_id} verification failed")

            # Create restore record
            self.repository.update_backup_status(
                backup_id,
                BackupStatus.RESTORED.value,
            )

            # Copy database back
            if os.path.exists(backup.file_path):
                db_backup_file = os.path.join(backup.file_path, "database.db")
                if os.path.exists(db_backup_file):
                    # Backup current database
                    if os.path.exists(self.database_path):
                        backup_current = f"{self.database_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        shutil.copy2(self.database_path, backup_current)

                    # Restore
                    shutil.copy2(db_backup_file, self.database_path)

            return {
                "backup_id": backup_id,
                "name": backup.name,
                "restored_at": datetime.now().isoformat(),
                "database_path": self.database_path,
            }

    def _verify_backup(self, backup) -> bool:
        """Verify backup integrity.

        Args:
            backup: Backup entity

        Returns:
            True if backup is valid
        """
        if not os.path.exists(backup.file_path):
            return False

        # Calculate checksum
        checksum = hashlib.sha256()
        for root, _dirs, files in os.walk(backup.file_path):
            for file in sorted(files):
                file_path = os.path.join(root, file)
                with open(file_path, "rb") as f:
                    checksum.update(f.read())

        return checksum.hexdigest() == backup.checksum

    def get_restore_point(self, backup_id: int) -> dict[str, Any] | None:
        """Get restore point information.

        Args:
            backup_id: Backup ID

        Returns:
            Restore point information
        """
        backups = self.repository.list_backups()
        backup = next((b for b in backups if b.id == backup_id), None)

        if not backup:
            return None

        return {
            "id": backup.id,
            "name": backup.name,
            "type": backup.backup_type,
            "size_mb": backup.file_size_mb,
            "created_at": backup.created_at.isoformat() if backup.created_at else None,
            "is_valid": self._verify_backup(backup),
        }

    def list_restore_points(self) -> list[dict[str, Any]]:
        """List available restore points.

        Returns:
            List of restore points
        """
        completed_backups = self.repository.list_backups(status="completed")
        restore_points = []

        for backup in completed_backups:
            restore_points.append(
                {
                    "id": backup.id,
                    "name": backup.name,
                    "type": backup.backup_type,
                    "size_mb": backup.file_size_mb,
                    "created_at": backup.created_at.isoformat() if backup.created_at else None,
                    "is_valid": self._verify_backup(backup),
                }
            )

        return restore_points
