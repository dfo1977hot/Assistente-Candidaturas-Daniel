"""Tests for LearningService."""

from __future__ import annotations

from types import SimpleNamespace

from acd.services.learning.learning_service import LearningService


class FakeRepository:
    """Fake repository."""

    def __init__(self) -> None:
        self.outcomes = []
        self.patterns = []
        self.insights = []

    # ---------- Outcome ----------

    def create_outcome(self, **kwargs):
        outcome = SimpleNamespace(id=1, **kwargs)
        self.outcomes.append(outcome)
        return outcome

    def list_outcomes(self, days_back: int, limit: int):
        return self.outcomes

    # ---------- Patterns ----------

    def create_pattern(self, **kwargs):
        pattern = SimpleNamespace(id=len(self.patterns) + 1, **kwargs)
        self.patterns.append(pattern)
        return pattern

    def list_patterns(self, is_active: bool, limit: int):
        return self.patterns

    # ---------- Insights ----------

    def create_insight(self, **kwargs):
        insight = SimpleNamespace(id=len(self.insights) + 1, **kwargs)
        self.insights.append(insight)
        return insight

    def list_insights(self, **kwargs):
        return []

    # ---------- Learning Records ----------

    def list_records(self, status: str, limit: int):
        return []

    def list_hypotheses(self, status: str, limit: int):
        return []

    def approve_record(self, record_id: int, notes: str):
        return True

    def reject_record(self, record_id: int, notes: str):
        return True

    # ---------- Statistics ----------

    def get_statistics(self):
        return {}


class FakeEngine:
    """Fake learning engine."""

    def process_outcome(
        self,
        outcome,
        *,
        auto_detect_patterns: bool,
    ):
        return {
            "success": True,
        }

    def detect_patterns(
        self,
        outcomes,
        pattern_types,
    ):
        return [
            {
                "pattern": {
                    "name": "Python",
                    "description": "Python aparece com frequência.",
                    "type": "skill",
                    "criteria": {},
                    "evidence_count": 10,
                    "confidence": 0.95,
                },
                "requires_approval": False,
            }
        ]

    def generate_insights(
        self,
        patterns,
        *,
        max_insights,
    ):
        if not patterns:
            return []

        return [
            {
                "insight": {
                    "title": "Invista em Python",
                    "description": "Competência recorrente.",
                    "insight_type": "skill",
                    "expected_impact": "high",
                    "confidence": 0.90,
                    "recommendations": [
                        "Estudar Python",
                    ],
                },
                "requires_approval": False,
            }
        ]

    def get_statistics(self):
        return {}

    def get_health_report(self):
        return {
            "status": "healthy",
        }


def create_service() -> LearningService:
    """Create service using fake dependencies."""

    service = LearningService.__new__(LearningService)

    service.repository = FakeRepository()
    service.engine = FakeEngine()
    service.session = None

    return service


# ==========================================================
# register_outcome
# ==========================================================


def test_register_outcome() -> None:
    """Should register and process outcome."""

    service = create_service()

    result = service.register_outcome(
        outcome_type="application",
        result="success",
        company="OpenAI",
        position_title="Engineer",
    )

    assert result["success"] is True
    assert result["outcome_id"] == 1


# ==========================================================
# detect_patterns
# ==========================================================


def test_detect_patterns_without_outcomes() -> None:
    """Should return zero patterns."""

    service = create_service()

    result = service.detect_patterns()

    assert result["success"] is True
    assert result["patterns_detected"] == 0
    assert result["patterns"] == []


def test_detect_patterns() -> None:
    """Should detect and persist patterns."""

    service = create_service()

    service.repository.outcomes.append(SimpleNamespace(id=1))

    result = service.detect_patterns()

    assert result["success"] is True
    assert result["patterns_detected"] == 1
    assert len(service.repository.patterns) == 1
    assert service.repository.patterns[0].name == "Python"


# ==========================================================
# generate_insights
# ==========================================================


def test_generate_insights_without_patterns() -> None:
    """Should return empty insight list."""

    service = create_service()

    result = service.generate_insights()

    assert result["success"] is True
    assert result["insights_generated"] == 0
    assert result["insights"] == []


def test_generate_insights() -> None:
    """Should generate and persist insights."""

    service = create_service()

    service.repository.patterns.append(
        SimpleNamespace(
            name="Python",
            description="desc",
            pattern_type="skill",
            criteria={},
            evidence_count=5,
            confidence=0.9,
        )
    )

    result = service.generate_insights()

    assert result["success"] is True
    assert result["insights_generated"] == 1
    assert len(service.repository.insights) == 1
    assert service.repository.insights[0].title == "Invista em Python"


# ==========================================================
# get_pending_approvals
# ==========================================================


def test_get_pending_approvals() -> None:
    """Should return pending records and hypotheses."""

    service = create_service()

    service.repository.list_records = lambda status, limit: [
        "record1",
        "record2",
    ]

    service.repository.list_hypotheses = lambda status, limit: [
        "hyp1",
    ]

    result = service.get_pending_approvals()

    assert result["learning_records"] == [
        "record1",
        "record2",
    ]
    assert result["hypotheses"] == [
        "hyp1",
    ]
    assert result["total_pending"] == 3


# ==========================================================
# approve_learning
# ==========================================================


def test_approve_learning() -> None:
    """Should delegate approval to repository."""

    service = create_service()

    service.repository.approve_record = lambda record_id, notes: True

    assert service.approve_learning(
        1,
        "approved",
    )


# ==========================================================
# reject_learning
# ==========================================================


def test_reject_learning() -> None:
    """Should delegate rejection to repository."""

    service = create_service()

    service.repository.reject_record = lambda record_id, notes: True

    assert service.reject_learning(
        1,
        "rejected",
    )


# ==========================================================
# get_recommendations
# ==========================================================


def test_get_recommendations() -> None:
    """Should flatten recommendations."""

    service = create_service()

    insight = SimpleNamespace(
        recommendations=[
            "Python",
            "SQL",
        ]
    )

    service.repository.list_insights = lambda **kwargs: [
        insight,
    ]

    result = service.get_recommendations()

    assert result == [
        "Python",
        "SQL",
    ]


# ==========================================================
# get_statistics
# ==========================================================


def test_get_statistics() -> None:
    """Should merge repository and engine statistics."""

    service = create_service()

    service.repository.get_statistics = lambda: {
        "patterns": 5,
    }

    service.engine.get_statistics = lambda: {
        "processed": 20,
    }

    result = service.get_statistics()

    assert result["patterns"] == 5
    assert result["processed"] == 20
    assert "timestamp" in result


# ==========================================================
# get_learning_health
# ==========================================================


def test_get_learning_health() -> None:
    """Should delegate health report."""

    service = create_service()

    service.engine.get_health_report = lambda: {
        "status": "healthy",
    }

    result = service.get_learning_health()

    assert result == {
        "status": "healthy",
    }