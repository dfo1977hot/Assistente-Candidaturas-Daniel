from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from acd.core.logger import logger
from acd.domain.ats_evaluation import (
    ATSEvaluationInput,
    ATSEvaluationResult,
    ATSEvaluator,
)
from acd.domain.entities.ats_score import ATSScore
from acd.domain.entities.curriculum import Curriculum
from acd.domain.entities.job_profile import JobProfile
from acd.domain.entities.recommendation import Recommendation
from acd.domain.entities.score_detail import ScoreDetail
from acd.domain.entities.skill_gap import SkillGap
from acd.infrastructure.repositories.ats_repository import ATSRepository


class ScoreEngine(Protocol):
    """Interface para motores de pontuação."""

    def calculate(
        self,
        *,
        curriculum_skills: list[str],
        job_skills: list[str],
        curriculum_experience: int,
        job_experience: int,
        curriculum_languages: list[str],
        job_languages: list[str],
        curriculum_certifications: list[str],
        job_certifications: list[str],
        desired_skills: list[str],
    ) -> dict[str, object]: ...


class RecommendationStrategy(Protocol):
    """Interface para estratégias de recomendação."""

    def generate(
        self,
        *,
        missing_skills: list[str],
        desired_skills: list[str],
        curriculum_strengths: list[str],
    ) -> list[str]: ...


@dataclass
class WeightConfiguration:
    """Pesos configuráveis para o ATS."""

    technical_skills: float = 0.40
    experience: float = 0.20
    education: float = 0.10
    languages: float = 0.10
    certifications: float = 0.10
    desired_skills: float = 0.10


class WeightConfigurationService:
    """Serviço de configuração de pesos do ATS."""

    def __init__(self, config: WeightConfiguration | None = None) -> None:
        self.config = config or WeightConfiguration()

    def get_config(self) -> WeightConfiguration:
        return self.config


class RuleBasedSimilarityEngine:
    """Motor de similaridade rudimentar para o ATS."""

    def calculate(self, left: str, right: str) -> float:
        normalized_left = left.lower().strip()
        normalized_right = right.lower().strip()
        if normalized_left == normalized_right:
            return 1.0
        if normalized_left in normalized_right or normalized_right in normalized_left:
            return 0.85
        return 0.2


class RuleBasedScoreEngine:
    """Motor de pontuação baseado em regras determinísticas."""

    def __init__(
        self,
        similarity_engine: RuleBasedSimilarityEngine | None = None,
        weight_config: WeightConfiguration | None = None,
    ) -> None:
        self.similarity_engine = similarity_engine or RuleBasedSimilarityEngine()
        self.weight_config = weight_config or WeightConfiguration()

    def calculate(
        self,
        *,
        curriculum_skills: list[str],
        job_skills: list[str],
        curriculum_experience: int,
        job_experience: int,
        curriculum_languages: list[str],
        job_languages: list[str],
        curriculum_certifications: list[str],
        job_certifications: list[str],
        desired_skills: list[str],
    ) -> dict[str, object]:
        matched_skills: list[str] = []
        normalized_job_skills = {skill.lower().strip(): skill for skill in job_skills if skill}
        for skill in curriculum_skills:
            normalized_skill = skill.lower().strip()
            if normalized_skill in normalized_job_skills:
                matched_skills.append(skill)
                continue
            if any(
                self.similarity_engine.calculate(skill, candidate) >= 0.8
                for candidate in normalized_job_skills.values()
            ):
                matched_skills.append(skill)

        technical_ratio = len(matched_skills) / max(1, len(curriculum_skills))
        technical_score = round(min(40.0, technical_ratio * 40.0), 2)
        experience_ratio = min(1.0, curriculum_experience / max(1, job_experience))
        language_ratio = len(set(curriculum_languages) & set(job_languages)) / max(
            1, len(job_languages)
        )
        certification_ratio = len(set(curriculum_certifications) & set(job_certifications)) / max(
            1, len(job_certifications)
        )
        desired_ratio = len(set(desired_skills) & set(curriculum_skills)) / max(
            1, len(desired_skills)
        )
        formation_ratio = 1.0 if curriculum_skills else 0.0
        experience_score = round(experience_ratio * 20, 2)
        formation_score = round(formation_ratio * 10, 2)
        language_score = round(language_ratio * 10, 2)
        certification_score = round(certification_ratio * 10, 2)
        desired_score = round(desired_ratio * 10, 2)

        total_score = round(
            (
                (technical_score / 40 * 100) * self.weight_config.technical_skills
                + (experience_score / 20 * 100) * self.weight_config.experience
                + (formation_score / 10 * 100) * self.weight_config.education
                + (language_score / 10 * 100) * self.weight_config.languages
                + (certification_score / 10 * 100) * self.weight_config.certifications
                + (desired_score / 10 * 100) * self.weight_config.desired_skills
            ),
            2,
        )

        return {
            "total_score": total_score,
            "criteria": {
                "competencias_tecnicas": {
                    "score": technical_score,
                    "max_score": 40,
                    "weight": self.weight_config.technical_skills,
                },
                "experiencia": {
                    "score": experience_score,
                    "max_score": 20,
                    "weight": self.weight_config.experience,
                },
                "formacao": {
                    "score": formation_score,
                    "max_score": 10,
                    "weight": self.weight_config.education,
                },
                "idiomas": {
                    "score": language_score,
                    "max_score": 10,
                    "weight": self.weight_config.languages,
                },
                "certificacoes": {
                    "score": certification_score,
                    "max_score": 10,
                    "weight": self.weight_config.certifications,
                },
                "desejaveis": {
                    "score": desired_score,
                    "max_score": 10,
                    "weight": self.weight_config.desired_skills,
                },
            },
            "matched_skills": matched_skills,
        }


class GapAnalysisEngine:
    """Identifica lacunas entre currículo e vaga."""

    def analyze(
        self,
        *,
        curriculum_skills: list[str],
        job_skills: list[str],
        desired_skills: list[str],
    ) -> dict[str, list[str]]:
        curriculum_lookup = {skill.casefold(): skill for skill in curriculum_skills if skill}
        missing_skills: list[str] = []
        for skill in job_skills:
            if skill and skill.casefold() not in curriculum_lookup:
                missing_skills.append(skill)

        return {
            "missing_skills": list(dict.fromkeys(missing_skills)),
            "desired_skills": [
                skill
                for skill in list(dict.fromkeys(desired_skills))
                if skill and skill.casefold() not in curriculum_lookup
            ],
        }


class ExplainabilityEngine:
    """Gera uma explicação textual e estruturada do score."""

    def build(
        self, *, total_score: int, criteria: dict[str, dict[str, float]]
    ) -> dict[str, object]:
        details = [
            {
                "label": "Competências Técnicas",
                "score": criteria.get("competencias_tecnicas", {}).get("score", 0),
                "max_score": criteria.get("competencias_tecnicas", {}).get("max_score", 40),
            },
            {
                "label": "Experiência",
                "score": criteria.get("experiencia", {}).get("score", 0),
                "max_score": criteria.get("experiencia", {}).get("max_score", 20),
            },
            {
                "label": "Idiomas",
                "score": criteria.get("idiomas", {}).get("score", 0),
                "max_score": criteria.get("idiomas", {}).get("max_score", 10),
            },
            {
                "label": "Formação",
                "score": criteria.get("formacao", {}).get("score", 0),
                "max_score": criteria.get("formacao", {}).get("max_score", 10),
            },
            {
                "label": "Certificações",
                "score": criteria.get("certificacoes", {}).get("score", 0),
                "max_score": criteria.get("certificacoes", {}).get("max_score", 10),
            },
            {
                "label": "Desejáveis",
                "score": criteria.get("desejaveis", {}).get("score", 0),
                "max_score": criteria.get("desejaveis", {}).get("max_score", 10),
            },
        ]
        return {"total_score": total_score, "details": details}


class RuleBasedRecommendationStrategy:
    """Estratégia de recomendação baseada em padrões determinísticos."""

    def generate(
        self,
        *,
        missing_skills: list[str],
        desired_skills: list[str],
        curriculum_strengths: list[str],
    ) -> list[str]:
        recommendations: list[str] = []
        for skill in missing_skills[:3]:
            recommendations.append(f"Adicionar {skill} no currículo.")
        for skill in desired_skills[:2]:
            recommendations.append(f"Destacar experiência com {skill}.")
        for strength in curriculum_strengths[:2]:
            recommendations.append(f"Destacar experiência com {strength} no resumo.")
        return recommendations


class ATSService:
    """Serviço principal do ATS Engine."""

    def __init__(
        self,
        repository: ATSRepository | None = None,
        score_engine: ScoreEngine | None = None,
        gap_engine: GapAnalysisEngine | None = None,
        explanation_engine: ExplainabilityEngine | None = None,
        recommendation_strategy: RecommendationStrategy | None = None,
    ) -> None:
        self.repository = repository or ATSRepository()
        self.score_engine = score_engine or RuleBasedScoreEngine()
        self.gap_engine = gap_engine or GapAnalysisEngine()
        self.explanation_engine = explanation_engine or ExplainabilityEngine()
        self.recommendation_strategy = recommendation_strategy or RuleBasedRecommendationStrategy()
        self.weight_configuration_service = WeightConfigurationService()

    def compare_curriculum(
        self, *, curriculum: Curriculum, job_profile: JobProfile
    ) -> dict[str, object]:
        """Compara um currículo com um perfil de vaga e persiste o resultado."""
        result = self.evaluate(self._to_evaluation_input(curriculum, job_profile))
        explanation = self.explanation_engine.build(
            total_score=int(result.total_score), criteria=self._criteria_mapping(result)
        )
        saved_score = self._persist_evaluation(curriculum.id, job_profile.id, result)

        logger.info("Score ATS calculado: %s", saved_score.total_score)
        return {
            "total_score": saved_score.total_score,
            "gaps": {
                "missing_skills": list(result.missing_skills),
                "desired_skills": list(result.desired_skills),
            },
            "recommendations": list(result.recommendations),
            "explanation": explanation,
        }

    def evaluate(self, evaluation_input: ATSEvaluationInput) -> ATSEvaluationResult:
        """Calculate ATS information without ORM access or persistence."""
        return ATSEvaluator(
            self.score_engine,
            self.gap_engine,
            self.recommendation_strategy,
        ).evaluate(evaluation_input)

    def _to_evaluation_input(
        self, curriculum: Curriculum, job_profile: JobProfile
    ) -> ATSEvaluationInput:
        job_technologies = self._split_list(job_profile.technologies or "")
        job_methodologies = self._split_list(job_profile.methodologies or "")
        return ATSEvaluationInput(
            resume_content=curriculum.description or "",
            job_skills=tuple(self._collect_job_skills(job_profile)),
            desired_skills=tuple(job_technologies + job_methodologies),
            job_languages=tuple(self._split_list(job_profile.languages or "")),
            job_certifications=tuple(self._split_list(job_profile.certifications or "")),
        )

    def _persist_evaluation(
        self,
        curriculum_id: int,
        job_profile_id: int,
        result: ATSEvaluationResult,
    ) -> ATSScore:
        score = self.repository.save_score(
            ATSScore(
                curriculum_id=curriculum_id,
                job_profile_id=job_profile_id,
                total_score=result.total_score,
            )
        )
        criteria = self._criteria_mapping(result)
        self._persist_details(score.id, criteria)
        self._persist_gaps(
            score.id,
            {
                "missing_skills": list(result.missing_skills),
                "desired_skills": list(result.desired_skills),
            },
        )
        self._persist_recommendations(score.id, list(result.recommendations))
        return score

    @staticmethod
    def _criteria_mapping(result: ATSEvaluationResult) -> dict[str, dict[str, float]]:
        return {
            criterion.name: {
                "score": criterion.score,
                "max_score": criterion.max_score,
                "weight": criterion.weight,
            }
            for criterion in result.criteria
        }

    def get_history(self) -> list[ATSScore]:
        """Retorna o histórico de comparações."""
        return self.repository.get_history()

    def get_statistics(self) -> dict[str, object]:
        """Retorna estatísticas do histórico ATS."""
        return self.repository.get_statistics()

    def _split_list(self, values: str) -> list[str]:
        return [item.strip() for item in values.split(",") if item and item.strip()]

    def _collect_job_skills(self, job_profile: JobProfile) -> list[str]:
        collected: list[str] = []
        for value in [
            job_profile.skills,
            job_profile.technologies,
            job_profile.methodologies,
            job_profile.keywords,
        ]:
            collected.extend(self._split_list(value or ""))
        return list(dict.fromkeys(collected))

    def _persist_details(self, score_id: int, criteria: dict[str, object]) -> None:
        for criterion, values in criteria.items():
            detail = ScoreDetail(
                score_id=score_id,
                criterion=criterion,
                score=float(values["score"]),
                max_score=float(values["max_score"]),
                weight=float(values["weight"]),
            )
            self.repository.save_detail(detail)

    def _persist_gaps(self, score_id: int, gaps: dict[str, list[str]]) -> None:
        for gap_type, skills in gaps.items():
            for skill in skills:
                self.repository.save_gap(
                    SkillGap(
                        score_id=score_id,
                        skill_name=skill,
                        gap_type="missing" if gap_type == "missing_skills" else "desired",
                    )
                )

    def _persist_recommendations(self, score_id: int, recommendations: list[str]) -> None:
        for message in recommendations:
            self.repository.save_recommendation(Recommendation(score_id=score_id, message=message))
