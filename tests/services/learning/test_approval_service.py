"""Tests for ApprovalService."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from acd.domain.learning.learning_record import LearningRecordStatus
from acd.services.learning.approval_service import ApprovalService


class FakeSession:
    """Fake SQLAlchemy session."""

    def __init__(self) -> None:
        self.commits = 0

    def commit(self) -> None:
        self.commits += 1


class FakeRecord:
    """Fake learning record."""

    def __init__(
        self,
        *,
        record_id: int = 1,
        status: str = LearningRecordStatus.DETECTED.value,
        created_at: datetime | None = None,
    ) -> None:
        self.id = record_id
        self.status = status
        self.source = "LinkedIn"
        self.source_type = "application"
        self.description = "Learning"
        self.confidence = 0.9
        self.evidence = ["item"]
        self.created_at = created_at or datetime.now(UTC)

    def approve(self, notes: str = "") -> None:
        self.status = LearningRecordStatus.APPROVED.value

    def reject(self, notes: str = "") -> None:
        self.status = LearningRecordStatus.REJECTED.value

    def is_approved(self) -> bool:
        return self.status == LearningRecordStatus.APPROVED.value


class FakeHypothesis:
    """Fake hypothesis."""

    def __init__(self) -> None:
        self.id = 1
        self.status = "PROPOSED"

    def confirm(self, notes: str = "") -> None:
        self.status = "CONFIRMED"

    def reject(self, notes: str = "") -> None:
        self.status = "REJECTED"


class FakeRepository:
    """Fake repository."""

    def __init__(self) -> None:
        self.session = FakeSession()
        self.records: list[FakeRecord] = []
        self.hypothesis: FakeHypothesis | None = FakeHypothesis()

    def list_records(self, **kwargs):
        return self.records

    def get_record(self, record_id: int):
        for record in self.records:
            if record.id == record_id:
                return record
        return None

    def get_hypothesis(self, hypothesis_id: int):
        return self.hypothesis


def create_service() -> ApprovalService:
    """Create service."""

    service = ApprovalService.__new__(ApprovalService)
    service.repository = FakeRepository()
    return service


# ==========================================================
# pending approvals
# ==========================================================


def test_get_pending_approvals() -> None:
    service = create_service()

    service.repository.records.append(FakeRecord())

    result = service.get_pending_approvals()

    assert len(result) == 1
    assert result[0]["type"] == "learning_record"


# ==========================================================
# approve record
# ==========================================================


def test_approve_learning_record() -> None:
    service = create_service()

    service.repository.records.append(FakeRecord())

    result = service.approve_learning_record(1)

    assert result["success"] is True
    assert service.repository.session.commits == 1


def test_approve_learning_record_not_found() -> None:
    service = create_service()

    result = service.approve_learning_record(99)

    assert result["success"] is False


# ==========================================================
# reject record
# ==========================================================


def test_reject_learning_record() -> None:
    service = create_service()

    service.repository.records.append(FakeRecord())

    result = service.reject_learning_record(1)

    assert result["success"] is True


def test_reject_learning_record_not_found() -> None:
    service = create_service()

    result = service.reject_learning_record(10)

    assert result["success"] is False


# ==========================================================
# hypothesis
# ==========================================================


def test_approve_hypothesis() -> None:
    service = create_service()

    result = service.approve_hypothesis(1)

    assert result["success"] is True


def test_reject_hypothesis() -> None:
    service = create_service()

    result = service.reject_hypothesis(1)

    assert result["success"] is True


def test_hypothesis_not_found() -> None:
    service = create_service()

    service.repository.hypothesis = None

    result = service.approve_hypothesis(1)

    assert result["success"] is False


# ==========================================================
# bulk approve
# ==========================================================


def test_bulk_approve() -> None:
    service = create_service()

    service.repository.records.extend(
        [
            FakeRecord(record_id=1),
            FakeRecord(record_id=2),
        ]
    )

    result = service.bulk_approve([1, 2])

    assert result["approved"] == 2
    assert result["failed"] == 0


def test_bulk_approve_missing_record() -> None:
    service = create_service()

    service.repository.records.append(FakeRecord(record_id=1))

    result = service.bulk_approve([1, 2])

    assert result["approved"] == 1
    assert result["failed"] == 1


# ==========================================================
# statistics
# ==========================================================


def test_get_approval_statistics() -> None:
    service = create_service()

    service.repository.records.extend(
        [
            FakeRecord(status=LearningRecordStatus.APPROVED.value),
            FakeRecord(status=LearningRecordStatus.REJECTED.value),
            FakeRecord(status=LearningRecordStatus.DETECTED.value),
        ]
    )

    stats = service.get_approval_statistics()

    assert stats["total_records"] == 3
    assert stats["approved"] == 1
    assert stats["pending"] == 1
    assert stats["rejected"] == 1


def test_statistics_empty() -> None:
    service = create_service()

    stats = service.get_approval_statistics()

    assert stats["approval_rate"] == 0


# ==========================================================
# archive
# ==========================================================


def test_archive_old_records() -> None:
    service = create_service()

    old = FakeRecord(
        status=LearningRecordStatus.APPROVED.value,
        created_at=datetime.now(UTC) - timedelta(days=120),
    )

    service.repository.records.append(old)

    result = service.archive_old_records()

    assert result["archived"] == 1
    assert old.status == LearningRecordStatus.ARCHIVED.value


def test_archive_does_not_archive_recent_records() -> None:
    service = create_service()

    service.repository.records.append(
        FakeRecord(
            status=LearningRecordStatus.APPROVED.value,
            created_at=datetime.now(UTC),
        )
    )

    result = service.archive_old_records()

    assert result["archived"] == 0