from datetime import UTC, datetime, timedelta
import os
import tempfile

import pytest

from acd.database import database as database_module
from acd.infrastructure.career.recommendation_engine import RecommendationRankingEngine
from acd.infrastructure.career.rule_engine import CareerRuleEngine
from acd.infrastructure.repositories.career_repository import CareerRepository
from acd.services.career_planning_service import CareerPlanningService
from acd.services.career_simulation_service import CareerSimulationService
from acd.services.gap_analysis_service import GapAnalysisService


@pytest.fixture
def temp_database(monkeypatch):
    """Create a temporary database for testing."""
    temp_dir = tempfile.mkdtemp(prefix="acd-career-", dir=".")
    db_path = os.path.join(temp_dir, "test_acd_career.db")
    monkeypatch.setattr("acd.database.database.DATABASE_URL", f"sqlite:///{db_path}")

    # Import all entities FIRST to register ORM metadata

    database_module.engine.dispose()
    database_module.engine = database_module.create_engine(
        f"sqlite:///{db_path}", echo=False, future=True
    )
    database_module.SessionLocal = database_module.sessionmaker(
        bind=database_module.engine, autoflush=False, autocommit=False
    )

    from acd.models.base import Base

    Base.metadata.create_all(database_module.engine)

    yield

    Base.metadata.drop_all(database_module.engine)


class TestCareerRepository:
    """Test career repository operations."""

    def test_create_goal(self, temp_database):
        """Test creating a career goal."""
        repo = CareerRepository()
        deadline = datetime.now(UTC) + timedelta(days=365)

        goal = repo.create_goal(
            target_role="Coordenador de Supply Chain",
            target_industry="Logística",
            deadline=deadline,
        )

        assert goal.id is not None
        assert goal.target_role == "Coordenador de Supply Chain"

    def test_list_goals(self, temp_database):
        """Test listing career goals."""
        repo = CareerRepository()
        deadline = datetime.now(UTC) + timedelta(days=365)

        repo.create_goal("Role 1", "Industry 1", deadline)
        repo.create_goal("Role 2", "Industry 2", deadline)

        goals = repo.list_goals()
        assert len(goals) >= 2

    def test_create_plan(self, temp_database):
        """Test creating a development plan."""
        repo = CareerRepository()
        deadline = datetime.now(UTC) + timedelta(days=365)

        goal = repo.create_goal("Role", "Industry", deadline)
        plan = repo.create_plan(
            goal_id=goal.id,
            title="Test Plan",
            start_date=datetime.now(UTC),
            target_date=deadline,
        )

        assert plan.id is not None
        assert plan.goal_id == goal.id

    def test_create_milestone(self, temp_database):
        """Test creating a milestone."""
        repo = CareerRepository()
        deadline = datetime.now(UTC) + timedelta(days=365)

        goal = repo.create_goal("Role", "Industry", deadline)
        plan = repo.create_plan(
            goal_id=goal.id,
            title="Test Plan",
            start_date=datetime.now(UTC),
            target_date=deadline,
        )
        milestone = repo.create_milestone(
            plan_id=plan.id,
            title="First Milestone",
            target_date=datetime.now(UTC) + timedelta(days=30),
            order_index=1,
        )

        assert milestone.id is not None
        assert milestone.plan_id == plan.id

    def test_create_skill_gap(self, temp_database):
        """Test creating a skill gap."""
        repo = CareerRepository()
        deadline = datetime.now(UTC) + timedelta(days=365)

        goal = repo.create_goal("Role", "Industry", deadline)
        gap = repo.create_gap(
            goal_id=goal.id,
            skill_name="Python",
            required_level=8.0,
            current_level=3.0,
        )

        assert gap.id is not None
        assert gap.skill_name == "Python"


class TestCareerRuleEngine:
    """Test career rule engine."""

    def test_analyze_compatibility(self):
        """Test compatibility analysis."""
        engine = CareerRuleEngine()
        profile = {
            "skills": {
                "Lean Manufacturing": 7,
                "Power BI": 6,
                "Excel Avançado": 8,
                "Gestão Logística": 8,
            },
            "certifications": [],
            "languages": {"Inglês": 6},
        }

        result = engine.analyze_compatibility(profile, "Coordenador de Supply Chain")

        assert "compatibility" in result
        assert result["compatibility"] > 0
        assert "gaps" in result

    def test_calculate_priority_score(self):
        """Test priority score calculation."""
        engine = CareerRuleEngine()
        score = engine.calculate_priority_score(impact=8, effort=4)

        assert score == 2.0

    def test_rank_recommendations(self):
        """Test recommendation ranking."""
        engine = CareerRuleEngine()
        recs = [
            {"impact": 5, "effort": 5, "alignment": 1.0},
            {"impact": 9, "effort": 3, "alignment": 1.0},
            {"impact": 3, "effort": 8, "alignment": 1.0},
        ]

        ranked = engine.rank_recommendations(recs)

        assert ranked[0]["priority_score"] > ranked[1]["priority_score"]


class TestRecommendationRankingEngine:
    """Test recommendation ranking engine."""

    def test_generate_recommendations(self):
        """Test recommendation generation."""
        engine = RecommendationRankingEngine()
        goal = {"target_role": "Coordenador de Supply Chain", "target_industry": "Logística"}
        gaps = [
            {"skill": "SAP S/4HANA", "current": 0, "required": 8, "severity": "critical"},
        ]

        recs = engine.generate_recommendations(goal, gaps)

        assert len(recs) > 0
        assert all("title" in rec for rec in recs)

    def test_simulate_scenario(self):
        """Test scenario simulation."""
        engine = RecommendationRankingEngine()
        recs = [
            {"title": "Rec 1", "impact": 8, "effort": 4, "duration_days": 60},
        ]

        result = engine.simulate_scenario(50, recs)

        assert result["projected_compatibility"] > result["current_compatibility"]


class TestCareerPlanningService:
    """Test career planning service."""

    def test_create_career_goal(self, temp_database):
        """Test creating a career goal."""
        service = CareerPlanningService()
        goal = service.create_career_goal(
            target_role="Supply Chain Manager",
            target_industry="Logistics",
            deadline_months=12,
        )

        assert goal["id"] is not None
        assert goal["target_role"] == "Supply Chain Manager"

    def test_list_active_goals(self, temp_database):
        """Test listing active goals."""
        service = CareerPlanningService()
        service.create_career_goal("Role 1", "Industry 1", 12)
        service.create_career_goal("Role 2", "Industry 2", 6)

        goals = service.list_active_goals()

        assert len(goals) >= 2

    def test_get_statistics(self, temp_database):
        """Test getting statistics."""
        service = CareerPlanningService()
        service.create_career_goal("Role 1", "Industry 1", 12, priority=1)
        service.create_career_goal("Role 2", "Industry 2", 12, priority=7)

        stats = service.get_statistics()

        assert stats["active_goals"] >= 2


class TestGapAnalysisService:
    """Test gap analysis service."""

    def test_analyze_goal(self, temp_database):
        """Test goal analysis."""
        planning_service = CareerPlanningService()
        gap_service = GapAnalysisService()

        goal = planning_service.create_career_goal(
            "Coordenador de Supply Chain",
            "Logística",
            12,
        )

        profile = {
            "skills": {"Lean Manufacturing": 7, "Power BI": 6},
            "certifications": [],
            "languages": {"Inglês": 5},
        }

        result = gap_service.analyze_goal(goal["id"], profile)

        assert "gaps_count" in result
        assert "compatibility" in result

    def test_estimate_timeline(self, temp_database):
        """Test timeline estimation."""
        planning_service = CareerPlanningService()
        gap_service = GapAnalysisService()

        goal = planning_service.create_career_goal(
            "Coordenador de Supply Chain",
            "Logística",
            12,
        )

        profile = {
            "skills": {"Lean Manufacturing": 7},
            "certifications": [],
            "languages": {"Inglês": 5},
        }

        gap_service.analyze_goal(goal["id"], profile)
        timeline = gap_service.estimate_timeline(goal["id"])

        assert "estimated_days" in timeline
        assert timeline["estimated_days"] >= 0


class TestCareerSimulationService:
    """Test career simulation service."""

    def test_simulate_skill_improvement(self):
        """Test simulating skill improvement."""
        service = CareerSimulationService()
        profile = {"skills": {"Python": 3}, "certifications": [], "languages": {}}

        result = service.simulate_skill_improvement(
            profile,
            "Coordenador de Supply Chain",
            "SAP S/4HANA",
            5,
        )

        assert "simulated_compatibility" in result
        assert result["improvement"] != 0

    def test_simulate_certification(self):
        """Test simulating certification."""
        service = CareerSimulationService()
        profile = {"skills": {}, "certifications": [], "languages": {}}

        result = service.simulate_certification(
            profile,
            "Coordenador de Supply Chain",
            "APICS CSCP",
        )

        assert "simulated_compatibility" in result

    def test_compare_scenarios(self):
        """Test comparing scenarios."""
        service = CareerSimulationService()
        profile = {"skills": {}, "certifications": [], "languages": {}}

        scenarios = [
            {"name": "Scenario 1", "skills": {"Python": 8}},
            {"name": "Scenario 2", "skills": {"Python": 5, "SQL": 6}},
        ]

        results = service.compare_scenarios(
            profile,
            "Coordenador de Supply Chain",
            scenarios,
        )

        assert len(results) == 2
        assert results[0]["name"] in [s["name"] for s in scenarios]
