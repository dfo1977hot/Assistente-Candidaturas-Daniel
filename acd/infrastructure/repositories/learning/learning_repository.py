"""Repository for learning records, insights, patterns, and hypotheses."""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from acd.domain.learning.hypothesis import Hypothesis, HypothesisStatus
from acd.domain.learning.insight import Insight
from acd.domain.learning.learning_record import (
    LearningRecord,
    LearningRecordStatus,
)
from acd.domain.learning.outcome import Outcome
from acd.domain.learning.pattern import Pattern


class LearningRepository:
    """Repository for learning domain entities."""

    def __init__(self, session: Session) -> None:
        """Initialize repository.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    # Learning Record operations
    def create_record(
        self,
        source: str,
        source_type: str,
        description: str,
        evidence: dict[str, Any],
        confidence: float = 0.5,
    ) -> LearningRecord:
        """Create learning record.

        Args:
            source: Source of learning
            source_type: Type of source
            description: Record description
            evidence: Evidence data
            confidence: Confidence level

        Returns:
            Created record
        """
        record = LearningRecord(
            source=source,
            source_type=source_type,
            description=description,
            evidence=evidence,
            confidence=confidence,
            status=LearningRecordStatus.DETECTED,
        )
        self.session.add(record)
        self.session.commit()
        return record

    def list_records(
        self,
        status: str | None = None,
        source_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[LearningRecord]:
        """List learning records.

        Args:
            status: Filter by status
            source_type: Filter by source type
            limit: Result limit
            offset: Result offset

        Returns:
            List of records
        """
        query = self.session.query(LearningRecord)

        if status:
            query = query.filter(LearningRecord.status == status)
        if source_type:
            query = query.filter(LearningRecord.source_type == source_type)

        return query.order_by(desc(LearningRecord.created_at)).limit(limit).offset(offset).all()

    def get_record(self, record_id: int) -> LearningRecord | None:
        """Get learning record by ID.

        Args:
            record_id: Record ID

        Returns:
            Record or None
        """
        return self.session.query(LearningRecord).filter(LearningRecord.id == record_id).first()

    def approve_record(self, record_id: int, notes: str = "") -> bool:
        """Approve learning record.

        Args:
            record_id: Record ID
            notes: Approval notes

        Returns:
            True if successful
        """
        record = self.get_record(record_id)
        if record:
            record.approve(notes)
            self.session.commit()
            return True
        return False

    def reject_record(self, record_id: int, notes: str = "") -> bool:
        """Reject learning record.

        Args:
            record_id: Record ID
            notes: Rejection notes

        Returns:
            True if successful
        """
        record = self.get_record(record_id)
        if record:
            record.reject(notes)
            self.session.commit()
            return True
        return False

    # Pattern operations
    def create_pattern(
        self,
        name: str,
        description: str,
        pattern_type: str,
        criteria: dict[str, Any],
        evidence_count: int = 0,
        confidence: float = 0.5,
    ) -> Pattern:
        """Create pattern.

        Args:
            name: Pattern name
            description: Pattern description
            pattern_type: Type of pattern
            criteria: Pattern criteria
            evidence_count: Number of evidence items
            confidence: Confidence level

        Returns:
            Created pattern
        """
        pattern = Pattern(
            name=name,
            description=description,
            pattern_type=pattern_type,
            criteria=criteria,
            evidence_count=evidence_count,
            confidence=confidence,
        )
        self.session.add(pattern)
        self.session.commit()
        return pattern

    def list_patterns(
        self,
        is_active: bool = True,
        pattern_type: str | None = None,
        limit: int = 100,
    ) -> list[Pattern]:
        """List patterns.

        Args:
            is_active: Filter by active status
            pattern_type: Filter by type
            limit: Result limit

        Returns:
            List of patterns
        """
        query = self.session.query(Pattern).filter(Pattern.is_active == is_active)

        if pattern_type:
            query = query.filter(Pattern.pattern_type == pattern_type)

        return query.order_by(desc(Pattern.confidence)).limit(limit).all()

    def get_pattern(self, pattern_id: int) -> Pattern | None:
        """Get pattern by ID.

        Args:
            pattern_id: Pattern ID

        Returns:
            Pattern or None
        """
        return self.session.query(Pattern).filter(Pattern.id == pattern_id).first()

    # Hypothesis operations
    def create_hypothesis(
        self,
        description: str,
        statement: str,
        confidence: float = 0.5,
        evidence_base: dict[str, Any] | None = None,
    ) -> Hypothesis:
        """Create hypothesis.

        Args:
            description: Description
            statement: Statement
            confidence: Confidence level
            evidence_base: Supporting evidence

        Returns:
            Created hypothesis
        """
        hypothesis = Hypothesis(
            description=description,
            statement=statement,
            confidence=confidence,
            evidence_base=evidence_base or {},
            status=HypothesisStatus.PROPOSED.value,
        )
        self.session.add(hypothesis)
        self.session.commit()
        return hypothesis

    def list_hypotheses(
        self,
        status: str | None = None,
        limit: int = 100,
    ) -> list[Hypothesis]:
        """List hypotheses.

        Args:
            status: Filter by status
            limit: Result limit

        Returns:
            List of hypotheses
        """
        query = self.session.query(Hypothesis)

        if status:
            query = query.filter(Hypothesis.status == status)

        return query.order_by(desc(Hypothesis.confidence)).limit(limit).all()

    def get_hypothesis(self, hypothesis_id: int) -> Hypothesis | None:
        """Get hypothesis by ID.

        Args:
            hypothesis_id: Hypothesis ID

        Returns:
            Hypothesis or None
        """
        return self.session.query(Hypothesis).filter(Hypothesis.id == hypothesis_id).first()

    def confirm_hypothesis(self, hypothesis_id: int, notes: str = "") -> bool:
        """Confirm hypothesis.

        Args:
            hypothesis_id: Hypothesis ID
            notes: Confirmation notes

        Returns:
            True if successful
        """
        hypothesis = self.get_hypothesis(hypothesis_id)
        if hypothesis:
            hypothesis.confirm(notes)
            self.session.commit()
            return True
        return False

    # Insight operations
    def create_insight(
        self,
        title: str,
        description: str,
        insight_type: str,
        expected_impact: str,
        confidence: float = 0.5,
        recommendations: list[dict[str, Any]] | None = None,
    ) -> Insight:
        """Create insight.

        Args:
            title: Title
            description: Description
            insight_type: Type of insight
            expected_impact: Expected impact
            confidence: Confidence level
            recommendations: Recommendations list

        Returns:
            Created insight
        """
        insight = Insight(
            title=title,
            description=description,
            insight_type=insight_type,
            expected_impact=expected_impact,
            confidence=confidence,
            origin="learning_engine",
            recommendations=recommendations or [],
        )
        self.session.add(insight)
        self.session.commit()
        return insight

    def list_insights(
        self,
        is_actionable: bool = True,
        is_applied: bool = False,
        limit: int = 100,
    ) -> list[Insight]:
        """List insights.

        Args:
            is_actionable: Filter by actionability
            is_applied: Filter by applied status
            limit: Result limit

        Returns:
            List of insights
        """
        query = self.session.query(Insight)

        if is_actionable is not None:
            query = query.filter(Insight.is_actionable == is_actionable)
        if is_applied is not None:
            query = query.filter(Insight.is_applied == is_applied)

        return query.order_by(desc(Insight.confidence)).limit(limit).all()

    def get_insight(self, insight_id: int) -> Insight | None:
        """Get insight by ID.

        Args:
            insight_id: Insight ID

        Returns:
            Insight or None
        """
        return self.session.query(Insight).filter(Insight.id == insight_id).first()

    def mark_insight_applied(self, insight_id: int) -> bool:
        """Mark insight as applied.

        Args:
            insight_id: Insight ID

        Returns:
            True if successful
        """
        insight = self.get_insight(insight_id)
        if insight:
            insight.mark_applied()
            self.session.commit()
            return True
        return False

    # Outcome operations
    def create_outcome(
        self, outcome_type: str, result: str, company: str, position_title: str, **kwargs
    ) -> Outcome:
        """Create outcome.

        Args:
            outcome_type: Type of outcome
            result: Result (success/failure/etc)
            company: Company name
            position_title: Position title
            **kwargs: Additional fields

        Returns:
            Created outcome
        """
        outcome = Outcome(
            outcome_type=outcome_type,
            result=result,
            company=company,
            position_title=position_title,
            **kwargs,
        )
        self.session.add(outcome)
        self.session.commit()
        return outcome

    def list_outcomes(
        self,
        result: str | None = None,
        days_back: int = 90,
        limit: int = 500,
    ) -> list[Outcome]:
        """List outcomes.

        Args:
            result: Filter by result
            days_back: Days to look back
            limit: Result limit

        Returns:
            List of outcomes
        """
        cutoff_date = datetime.now(UTC) - timedelta(days=days_back)
        query = self.session.query(Outcome).filter(Outcome.created_at >= cutoff_date)

        if result:
            query = query.filter(Outcome.result == result)

        return query.order_by(desc(Outcome.recorded_date)).limit(limit).all()

    def get_statistics(self) -> dict[str, int]:
        """Get repository statistics.

        Returns:
            Statistics
        """
        return {
            "total_records": self.session.query(LearningRecord).count(),
            "approved_records": self.session.query(LearningRecord)
            .filter(LearningRecord.status == LearningRecordStatus.APPROVED)
            .count(),
            "patterns": self.session.query(Pattern).count(),
            "hypotheses": self.session.query(Hypothesis).count(),
            "insights": self.session.query(Insight).count(),
            "outcomes": self.session.query(Outcome).count(),
        }
