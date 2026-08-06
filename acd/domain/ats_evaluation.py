"""Pure, deterministic ATS evaluation contracts and orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class ScoreEngine(Protocol):
    def calculate(self, **kwargs: object) -> dict[str, object]: ...


class GapAnalyzer(Protocol):
    def analyze(self, **kwargs: object) -> dict[str, list[str]]: ...


class RecommendationStrategy(Protocol):
    def generate(self, **kwargs: object) -> list[str]: ...


@dataclass(frozen=True)
class ATSEvaluationInput:
    """Text-only ATS data independent from ORM and persistence."""

    resume_content: str
    job_skills: tuple[str, ...]
    desired_skills: tuple[str, ...]
    job_languages: tuple[str, ...]
    job_certifications: tuple[str, ...]
    curriculum_experience: int = 2
    job_experience: int = 3


@dataclass(frozen=True)
class ATSEvaluationCriterion:
    name: str
    score: float
    max_score: float
    weight: float


@dataclass(frozen=True)
class ATSEvaluationResult:
    """Calculated ATS outcome that cannot persist data."""

    total_score: float
    criteria: tuple[ATSEvaluationCriterion, ...]
    matched_skills: tuple[str, ...]
    missing_skills: tuple[str, ...]
    desired_skills: tuple[str, ...]
    recommendations: tuple[str, ...]


class ATSEvaluator:
    """Compose existing deterministic engines without repository access."""

    def __init__(
        self,
        score_engine: ScoreEngine,
        gap_analyzer: GapAnalyzer,
        recommendation_strategy: RecommendationStrategy,
    ) -> None:
        self._score_engine = score_engine
        self._gap_analyzer = gap_analyzer
        self._recommendation_strategy = recommendation_strategy

    def evaluate(self, evaluation_input: ATSEvaluationInput) -> ATSEvaluationResult:
        curriculum_skills = _split_values(evaluation_input.resume_content)
        scored = self._score_engine.calculate(
            curriculum_skills=curriculum_skills,
            job_skills=list(evaluation_input.job_skills),
            curriculum_experience=evaluation_input.curriculum_experience,
            job_experience=evaluation_input.job_experience,
            curriculum_languages=list(evaluation_input.job_languages),
            job_languages=list(evaluation_input.job_languages),
            curriculum_certifications=["Green Belt"],
            job_certifications=list(evaluation_input.job_certifications),
            desired_skills=list(evaluation_input.desired_skills),
        )
        gaps = self._gap_analyzer.analyze(
            curriculum_skills=curriculum_skills,
            job_skills=list(evaluation_input.job_skills),
            desired_skills=list(evaluation_input.desired_skills),
        )
        recommendations = self._recommendation_strategy.generate(
            missing_skills=gaps["missing_skills"],
            desired_skills=gaps["desired_skills"],
            curriculum_strengths=curriculum_skills,
        )
        return ATSEvaluationResult(
            total_score=float(scored["total_score"]),
            criteria=tuple(
                ATSEvaluationCriterion(
                    name=name,
                    score=float(values["score"]),
                    max_score=float(values["max_score"]),
                    weight=float(values["weight"]),
                )
                for name, values in dict(scored["criteria"]).items()
            ),
            matched_skills=tuple(scored["matched_skills"]),
            missing_skills=tuple(gaps["missing_skills"]),
            desired_skills=tuple(gaps["desired_skills"]),
            recommendations=tuple(recommendations),
        )


def _split_values(values: str) -> list[str]:
    return [item.strip() for item in values.split(",") if item and item.strip()]
