"""Approval service for managing learning approvals."""

from datetime import UTC, datetime, datetime
from typing import Any

from sqlalchemy.orm import Session

from acd.domain.learning.learning_record import LearningRecordStatus
from acd.infrastructure.repositories.learning import LearningRepository


class ApprovalService:
    """Service for managing learning approvals."""

    def __init__(self, session: Session) -> None:
        """Initialize approval service.

        Args:
            session: SQLAlchemy session
        """
        self.repository = LearningRepository(session)

    def get_pending_approvals(
        self,
        limit: int = 50,
        source_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get pending learning approvals.

        Args:
            limit: Maximum items to return
            source_type: Filter by source type

        Returns:
            List of pending items
        """
        records = self.repository.list_records(
            status=LearningRecordStatus.DETECTED.value,
            source_type=source_type,
            limit=limit,
        )

        result = []
        for record in records:
            result.append(
                {
                    "id": record.id,
                    "type": "learning_record",
                    "source": record.source,
                    "source_type": record.source_type,
                    "description": record.description,
                    "confidence": record.confidence,
                    "evidence": record.evidence,
                    "created_at": record.created_at.isoformat(),
                }
            )

        return result

    def approve_learning_record(
        self,
        record_id: int,
        approver_notes: str = "",
    ) -> dict[str, Any]:
        """Approve a learning record.

        Args:
            record_id: Record ID
            approver_notes: Notes from approver

        Returns:
            Approval result
        """
        record = self.repository.get_record(record_id)
        if not record:
            return {"success": False, "error": "Record not found"}

        record.approve(approver_notes)
        self.repository.session.commit()

        return {
            "success": True,
            "record_id": record_id,
            "status": record.status,
            "approved_at": datetime.now(UTC).isoformat(),
        }

    def reject_learning_record(
        self,
        record_id: int,
        rejection_notes: str = "",
    ) -> dict[str, Any]:
        """Reject a learning record.

        Args:
            record_id: Record ID
            rejection_notes: Notes from reviewer

        Returns:
            Rejection result
        """
        record = self.repository.get_record(record_id)
        if not record:
            return {"success": False, "error": "Record not found"}

        record.reject(rejection_notes)
        self.repository.session.commit()

        return {
            "success": True,
            "record_id": record_id,
            "status": record.status,
            "rejected_at": datetime.now(UTC).isoformat(),
        }

    def approve_hypothesis(
        self,
        hypothesis_id: int,
        confirmation_notes: str = "",
    ) -> dict[str, Any]:
        """Approve/confirm a hypothesis.

        Args:
            hypothesis_id: Hypothesis ID
            confirmation_notes: Confirmation notes

        Returns:
            Confirmation result
        """
        hypothesis = self.repository.get_hypothesis(hypothesis_id)
        if not hypothesis:
            return {"success": False, "error": "Hypothesis not found"}

        hypothesis.confirm(confirmation_notes)
        self.repository.session.commit()

        return {
            "success": True,
            "hypothesis_id": hypothesis_id,
            "status": hypothesis.status,
            "confirmed_at": datetime.now(UTC).isoformat(),
        }

    def reject_hypothesis(
        self,
        hypothesis_id: int,
        rejection_notes: str = "",
    ) -> dict[str, Any]:
        """Reject a hypothesis.

        Args:
            hypothesis_id: Hypothesis ID
            rejection_notes: Rejection notes

        Returns:
            Rejection result
        """
        hypothesis = self.repository.get_hypothesis(hypothesis_id)
        if not hypothesis:
            return {"success": False, "error": "Hypothesis not found"}

        hypothesis.reject(rejection_notes)
        self.repository.session.commit()

        return {
            "success": True,
            "hypothesis_id": hypothesis_id,
            "status": hypothesis.status,
            "rejected_at": datetime.now(UTC).isoformat(),
        }

    def bulk_approve(
        self,
        record_ids: list[int],
        notes: str = "",
    ) -> dict[str, Any]:
        """Approve multiple records at once.

        Args:
            record_ids: List of record IDs
            notes: Common notes

        Returns:
            Bulk approval result
        """
        approved = 0
        failed = 0

        for record_id in record_ids:
            try:
                record = self.repository.get_record(record_id)
                if record:
                    record.approve(notes)
                    approved += 1
                else:
                    failed += 1
            except Exception:
                failed += 1

        self.repository.session.commit()

        return {
            "success": True,
            "approved": approved,
            "failed": failed,
            "total": len(record_ids),
        }

    def get_approval_statistics(self) -> dict[str, Any]:
        """Get approval workflow statistics.

        Returns:
            Statistics
        """
        all_records = self.repository.list_records(limit=10000)

        stats = {
            "total_records": len(all_records),
            "approved": sum(1 for r in all_records if r.is_approved()),
            "rejected": sum(
                1 for r in all_records if r.status == LearningRecordStatus.REJECTED.value
            ),
            "pending": sum(
                1 for r in all_records if r.status == LearningRecordStatus.DETECTED.value
            ),
        }

        stats["approval_rate"] = (
            stats["approved"] / stats["total_records"] if stats["total_records"] > 0 else 0
        )

        return stats

    def archive_old_records(self, days: int = 90) -> dict[str, int]:
        """Archive learning records older than specified days.

        Args:
            days: Days threshold

        Returns:
            Count of archived records
        """
        from datetime import timedelta

        cutoff_date = datetime.now(UTC) - timedelta(days=days)

        records = self.repository.list_records(limit=10000)
        archived_count = 0

        for record in records:
            if (
                record.created_at < cutoff_date
                and record.status == LearningRecordStatus.APPROVED.value
            ):
                record.status = LearningRecordStatus.ARCHIVED.value
                archived_count += 1

        self.repository.session.commit()

        return {
            "archived": archived_count,
            "cutoff_date": cutoff_date.isoformat(),
        }
