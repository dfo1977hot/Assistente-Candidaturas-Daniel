import pytest

from acd.domain.ats_evaluation import ATSEvaluationInput
from acd.domain.entities.curriculum import Curriculum
from acd.domain.entities.job_profile import JobProfile
from acd.infrastructure.repositories.ats_repository import ATSRepository
from acd.services.ats_service import (
    ATSService,
    ExplainabilityEngine,
    GapAnalysisEngine,
    RuleBasedRecommendationStrategy,
    RuleBasedScoreEngine,
    RuleBasedSimilarityEngine as ATSRuleBasedSimilarityEngine,
    WeightConfiguration,
    WeightConfigurationService,
)
from acd.services.knowledge_service import RuleBasedSimilarityEngine


@pytest.fixture
def ats_setup(monkeypatch, tmp_path):
    temp_dir = tmp_path
    db_path = str(temp_dir / "test_acd.db")
    monkeypatch.setattr(
        "acd.database.database.DATABASE_URL",
        f"sqlite:///{db_path}",
    )

    import acd.database.database as database_module

    database_module.engine.dispose()
    database_module.engine = database_module.create_engine(
        f"sqlite:///{db_path}",
        echo=False,
        future=True,
    )
    database_module.SessionLocal = database_module.sessionmaker(
        bind=database_module.engine,
        autoflush=False,
        autocommit=False,
    )

    from acd.models.base import Base

    Base.metadata.drop_all(bind=database_module.engine)
    Base.metadata.create_all(bind=database_module.engine)

    yield ATSService(repository=ATSRepository())

    Base.metadata.drop_all(bind=database_module.engine)


def test_score_engine_uses_weighted_breakdown(ats_setup):
    engine = RuleBasedScoreEngine(similarity_engine=RuleBasedSimilarityEngine())
    score = engine.calculate(
        curriculum_skills=["Power BI", "Excel", "Lean"],
        job_skills=["Power BI", "Excel", "Lean", "SAP"],
        curriculum_experience=2,
        job_experience=3,
        curriculum_languages=["Inglês"],
        job_languages=["Inglês", "Espanhol"],
        curriculum_certifications=["Green Belt"],
        job_certifications=["Green Belt", "Black Belt"],
        desired_skills=["SAP"],
    )

    assert score["total_score"] >= 70
    assert score["criteria"]["competencias_tecnicas"]["score"] >= 30


def test_weight_configuration_service_returns_the_supplied_configuration() -> None:
    configuration = WeightConfiguration(technical_skills=0.5)

    assert WeightConfigurationService(configuration).get_config() is configuration


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        ("Python", "python", 1.0),
        ("SQL", "SQL Server", 0.85),
    ],
)
def test_ats_similarity_engine_handles_equal_and_contained_skills(
    left: str,
    right: str,
    expected: float,
) -> None:
    assert ATSRuleBasedSimilarityEngine().calculate(left, right) == expected


def test_score_engine_matches_a_skill_by_existing_similarity_rule() -> None:
    score = RuleBasedScoreEngine().calculate(
        curriculum_skills=["SQL"],
        job_skills=["SQL Server"],
        curriculum_experience=2,
        job_experience=3,
        curriculum_languages=[],
        job_languages=[],
        curriculum_certifications=[],
        job_certifications=[],
        desired_skills=[],
    )

    assert score["matched_skills"] == ["SQL"]


def test_gap_analysis_returns_missing_and_desired_skills(ats_setup):
    engine = GapAnalysisEngine()
    gaps = engine.analyze(
        curriculum_skills=["Power BI", "Excel", "Lean"],
        job_skills=["Power BI", "Excel", "Lean", "SAP", "SQL"],
        desired_skills=["Tableau", "VBA"],
    )

    assert "SAP" in gaps["missing_skills"]
    assert "Tableau" in gaps["desired_skills"]


def test_recommendation_engine_generates_rules(ats_setup):
    engine = RuleBasedRecommendationStrategy()
    recommendations = engine.generate(
        missing_skills=["SAP", "SQL"],
        desired_skills=["VBA"],
        curriculum_strengths=["Power BI", "Lean"],
    )

    assert any("SAP" in rec for rec in recommendations)
    assert any("VBA" in rec for rec in recommendations)


def test_explainability_engine_builds_breakdown(ats_setup):
    engine = ExplainabilityEngine()
    breakdown = engine.build(
        total_score=87,
        criteria={
            "competencias_tecnicas": {"score": 38, "max_score": 40},
            "experiencia": {"score": 18, "max_score": 20},
        },
    )

    assert breakdown["total_score"] == 87
    assert breakdown["details"][0]["label"] == "Competências Técnicas"


def test_ats_service_persists_results_and_history(ats_setup):
    service = ats_setup

    curriculum = Curriculum(name="Analista", description="Power BI, Excel, Lean, Six Sigma")
    job_profile = JobProfile(
        job_id=1,
        raw_description="Vaga analista com Power BI, Excel, Lean, SAP, SQL",
        skills="Power BI,Excel,Lean",
        technologies="Power BI,Excel",
        methodologies="Lean,Six Sigma",
        languages="Inglês",
        certifications="Green Belt",
        keywords="Power BI,Excel,Lean,SAP,SQL",
    )

    saved = service.compare_curriculum(curriculum=curriculum, job_profile=job_profile)

    assert saved["total_score"] >= 70
    assert saved["gaps"]["missing_skills"]
    assert service.get_history()
    assert service.get_statistics()["total_scores"] >= 1


class _WriteFailingRepository:
    """Fail if a pure evaluation reaches persistence."""

    def __getattr__(self, name: str):
        raise AssertionError(f"Pure evaluation must not call repository.{name}")


def test_pure_evaluation_accepts_text_and_never_persists() -> None:
    service = ATSService(repository=_WriteFailingRepository())

    result = service.evaluate(
        ATSEvaluationInput(
            resume_content="Python, SQL, Docker",
            job_skills=("Python", "SQL", "Kubernetes"),
            desired_skills=("Docker",),
            job_languages=("English",),
            job_certifications=("Green Belt",),
        )
    )

    assert result.total_score > 0
    assert result.criteria
    assert "Kubernetes" in result.missing_skills
    assert result.recommendations
