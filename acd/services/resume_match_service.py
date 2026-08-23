from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path
import re
import unicodedata

from acd.infrastructure.ai.providers import (
    AIProvider,
    SettingsConfiguredAIProvider,
)
from acd.services.settings_service import SettingsService


@dataclass(frozen=True, slots=True)
class ResumeMatchRequirement:
    """Aderência individual entre um requisito da vaga e o currículo."""

    category: str
    requirement: str
    evidence: str
    score: float
    status: str


@dataclass(frozen=True, slots=True)
class ResumeMatchDimension:
    """Pontuação agregada de uma dimensão da análise de aderência."""

    name: str
    score: float


@dataclass(frozen=True, slots=True)
class ResumeMatchResult:
    """Resultado explicável da comparação entre currículo e observações da vaga."""

    score: float
    adapted_score: float
    ats_score: float
    adapted_ats_score: float
    interview_probability_min: float
    interview_probability_max: float
    adapted_interview_probability_min: float
    adapted_interview_probability_max: float
    matched_keywords: tuple[str, ...]
    missing_keywords: tuple[str, ...]
    requirements: tuple[ResumeMatchRequirement, ...] = ()
    dimension_scores: tuple[ResumeMatchDimension, ...] = ()
    strengths: tuple[str, ...] = ()
    gaps: tuple[str, ...] = ()
    differentials: tuple[str, ...] = ()
    recommendation: str = ""
    adaptation_strategy: tuple[str, ...] = ()
    analyzed_at: str = ""

    @property
    def has_vacancy_description(self) -> bool:
        return bool(
            self.requirements
            or self.matched_keywords
            or self.missing_keywords
        )

    @property
    def overall_score(self) -> float:
        """Alias semântico para o score principal de aderência."""
        return self.score

    @property
    def classification(self) -> str:
        """Classificação qualitativa da aderência global."""
        if self.score >= 90:
            return "Muito alta"
        if self.score >= 75:
            return "Alta"
        if self.score >= 60:
            return "Moderada"
        if self.score >= 40:
            return "Baixa"
        return "Muito baixa"


class ResumeMatchService:
    """Compara currículo e vaga, persistindo resultados reutilizáveis."""

    _CACHE_VERSION = "v3"

    _STOP_WORDS = {
        "a",
        "ao",
        "aos",
        "as",
        "com",
        "como",
        "da",
        "das",
        "de",
        "do",
        "dos",
        "e",
        "em",
        "entre",
        "na",
        "nas",
        "no",
        "nos",
        "o",
        "os",
        "ou",
        "para",
        "por",
        "que",
        "se",
        "ser",
        "sua",
        "suas",
        "seu",
        "seus",
        "um",
        "uma",
        "the",
        "and",
        "for",
        "with",
        "from",
        "this",
        "that",
        "will",
        "you",
    }

    _CATEGORY_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
        (
            "Formação",
            (
                "formacao",
                "graduacao",
                "superior",
                "bacharel",
                "engenharia",
                "administracao",
                "tecnologia",
                "mba",
                "pos-graduacao",
            ),
        ),
        (
            "Idiomas",
            (
                "ingles",
                "english",
                "espanhol",
                "spanish",
                "idioma",
                "fluente",
                "avancado",
                "intermediario",
            ),
        ),
        (
            "Sistemas e ferramentas",
            (
                "sap",
                "excel",
                "power bi",
                "powerbi",
                "wms",
                "tms",
                "erp",
                "oracle",
                "totvs",
                "protheus",
                "sql",
                "python",
                "minitab",
                "ms project",
            ),
        ),
        (
            "Metodologias / Qualidade",
            (
                "lean",
                "six sigma",
                "kaizen",
                "pdca",
                "dmaic",
                "5s",
                "iso",
                "fmea",
                "apqp",
                "ppap",
                "cep",
                "spc",
                "msa",
                "8d",
                "a3",
                "ishikawa",
                "causa raiz",
                "melhoria continua",
                "qualidade",
            ),
        ),
        (
            "Experiência",
            (
                "experiencia",
                "vivencia",
                "anos",
                "lideranca",
                "liderar",
                "gestao",
                "coordenacao",
                "supervisao",
                "responsavel",
                "atuacao",
            ),
        ),
        (
            "Competências comportamentais",
            (
                "comunicacao",
                "negociacao",
                "stakeholder",
                "colaboracao",
                "adaptabilidade",
                "proatividade",
                "relacionamento",
                "resiliencia",
                "lideranca",
                "trabalho em equipe",
            ),
        ),
    )

    def __init__(
        self,
        storage_path: str | Path = "data/resume_match_results.json",
        *,
        settings_service: SettingsService | None = None,
        ai_provider: AIProvider | None = None,
    ) -> None:
        self.storage_path = Path(storage_path)
        self._settings_service = settings_service
        self._ai_provider = ai_provider

    def analyze(
        self,
        *,
        application: object,
        curriculum: object,
        force: bool = False,
    ) -> ResumeMatchResult:
        vacancy_text = self._vacancy_text(application)
        curriculum_text = self._curriculum_text(curriculum)

        cache_key = self._cache_key(
            application=application,
            curriculum=curriculum,
            vacancy_text=vacancy_text,
            curriculum_text=curriculum_text,
        )

        if not force:
            cached = self._load_cached(cache_key)
            if cached is not None:
                return cached

        result = self._calculate(
            vacancy_text=vacancy_text,
            curriculum_text=curriculum_text,
        )

        if result.has_vacancy_description:
            self._save_cached(cache_key, result)

        return result

    def analyze_semantic(
        self,
        *,
        application: object,
        curriculum: object,
        force: bool = False,
    ) -> ResumeMatchResult:
        """Analise semanticamente vaga e currículo usando a IA configurada.

        O resultado determinístico permanece como fallback obrigatório.
        Requisitos e evidências produzidos pela IA somente são aceitos quando
        correspondem a conteúdo efetivamente existente nos textos originais.
        """
        baseline = self.analyze(
            application=application,
            curriculum=curriculum,
            force=force,
        )

        if not baseline.has_vacancy_description:
            return baseline

        vacancy_text = self._vacancy_text(application)
        curriculum_text = self._curriculum_text(curriculum)

        semantic_cache_key = (
            "semantic:"
            + self._cache_key(
                application=application,
                curriculum=curriculum,
                vacancy_text=vacancy_text,
                curriculum_text=curriculum_text,
            )
        )

        if not force:
            cached = self._load_cached(semantic_cache_key)
            if cached is not None:
                return cached

        try:
            provider = self._semantic_ai_provider()

            raw = provider.generate_text(
                prompt=self._semantic_prompt(
                    vacancy_text=vacancy_text,
                    curriculum_text=curriculum_text,
                ),
                model="resume-match-semantic",
                temperature=0.0,
                max_tokens=6000,
                language="pt-BR",
            )

            result = self._semantic_result_from_raw(
                raw=raw,
                vacancy_text=vacancy_text,
                curriculum_text=curriculum_text,
                baseline=baseline,
            )
        except Exception:
            return baseline

        if result is baseline:
            return baseline

        self._save_cached(
            semantic_cache_key,
            result,
        )
        return result

    def _semantic_ai_provider(self) -> AIProvider:
        if self._ai_provider is not None:
            return self._ai_provider

        settings = (
            self._settings_service
            or SettingsService()
        )
        self._settings_service = settings
        self._ai_provider = SettingsConfiguredAIProvider(settings)
        return self._ai_provider

    def _semantic_prompt(
        self,
        *,
        vacancy_text: str,
        curriculum_text: str,
    ) -> str:
        return f"""
Você é um especialista em recrutamento, seleção, ATS e análise curricular.

Compare EXCLUSIVAMENTE a descrição da vaga e o currículo fornecidos abaixo.

REGRAS OBRIGATÓRIAS:

1. Não invente experiência, conhecimento, formação ou certificação.
2. Não considere conhecimento implícito como experiência comprovada.
3. Se a vaga pedir um módulo, tecnologia ou certificação específica diferente
   daquela presente no currículo, classifique apenas como aderência parcial
   quando houver relação real entre elas.
4. O campo "requirement" deve ser um trecho textual existente na VAGA.
5. O campo "evidence" deve ser um trecho textual existente no CURRÍCULO.
6. Quando não existir evidência, use exatamente:
   "Não evidenciado no currículo."
7. score deve variar de 0 a 100:
   - 85 a 100: atendimento forte/direto;
   - 65 a 84: aderente;
   - 40 a 64: parcial;
   - 1 a 39: baixa evidência;
   - 0: gap.
8. Não atribua 100% apenas porque uma palavra é semelhante.
9. Diferencie experiência profissional de formação ou curso.
10. Não use informações externas nem pesquisa web.
11. Retorne SOMENTE JSON válido, sem Markdown.

Categorias permitidas:
- Formação
- Experiência
- Conhecimentos técnicos
- Metodologias / Qualidade
- Sistemas e ferramentas
- Idiomas
- Competências comportamentais
- Requisitos específicos

Formato obrigatório:

{{
  "requirements": [
    {{
      "category": "categoria",
      "requirement": "trecho literal da vaga",
      "evidence": "trecho literal do currículo ou Não evidenciado no currículo.",
      "score": 0
    }}
  ]
}}

VAGA:
<<<VACANCY
{vacancy_text}
VACANCY

CURRÍCULO:
<<<CURRICULUM
{curriculum_text}
CURRICULUM
""".strip()

    def _semantic_result_from_raw(
        self,
        *,
        raw: str,
        vacancy_text: str,
        curriculum_text: str,
        baseline: ResumeMatchResult,
    ) -> ResumeMatchResult:
        payload = self._semantic_json_payload(raw)

        raw_requirements = payload.get("requirements", [])
        if not isinstance(raw_requirements, list):
            return baseline

        requirements = self._validated_semantic_requirements(
            raw_requirements=raw_requirements,
            vacancy_text=vacancy_text,
            curriculum_text=curriculum_text,
        )

        if not requirements:
            return baseline

        semantic_score = round(
            sum(item.score for item in requirements)
            / len(requirements),
            1,
        )

        ats_score = round(
            min(
                99.0,
                45.0 + (semantic_score * 0.54),
            ),
            1,
        )

        optimization_gain = min(
            22.0,
            (100.0 - semantic_score) * 0.72,
        )

        adapted_score = round(
            min(
                99.0,
                semantic_score + optimization_gain,
            ),
            1,
        )

        adapted_ats = round(
            min(
                99.0,
                ats_score + ((99.0 - ats_score) * 0.82),
            ),
            1,
        )

        current_min, current_max = self._probability_range(
            self._interview_estimate(
                ats_score=ats_score,
                technical_score=semantic_score,
            )
        )

        adapted_min, adapted_max = self._probability_range(
            self._interview_estimate(
                ats_score=adapted_ats,
                technical_score=adapted_score,
            )
        )

        return ResumeMatchResult(
            score=semantic_score,
            adapted_score=adapted_score,
            ats_score=ats_score,
            adapted_ats_score=adapted_ats,
            interview_probability_min=current_min,
            interview_probability_max=current_max,
            adapted_interview_probability_min=adapted_min,
            adapted_interview_probability_max=adapted_max,
            matched_keywords=baseline.matched_keywords,
            missing_keywords=baseline.missing_keywords,
            requirements=requirements,
            dimension_scores=self._build_dimension_scores(
                requirements
            ),
            strengths=self._build_strengths(
                requirements
            ),
            gaps=self._build_gaps(
                requirements
            ),
            differentials=baseline.differentials,
            recommendation=self._recommendation(
                semantic_score
            ),
            adaptation_strategy=self._build_adaptation_strategy(
                requirements=requirements,
                matched_keywords=baseline.matched_keywords,
            ),
            analyzed_at=datetime.now(UTC).isoformat(),
        )

    def _validated_semantic_requirements(
        self,
        *,
        raw_requirements: list[object],
        vacancy_text: str,
        curriculum_text: str,
    ) -> tuple[ResumeMatchRequirement, ...]:
        allowed_categories = {
            "Formação",
            "Experiência",
            "Conhecimentos técnicos",
            "Metodologias / Qualidade",
            "Sistemas e ferramentas",
            "Idiomas",
            "Competências comportamentais",
            "Requisitos específicos",
        }

        normalized_vacancy = self._normalize_text(
            vacancy_text
        )
        normalized_curriculum = self._normalize_text(
            curriculum_text
        )

        validated: list[ResumeMatchRequirement] = []

        for raw_item in raw_requirements:
            if not isinstance(raw_item, dict):
                continue

            requirement = str(
                raw_item.get("requirement", "")
                or ""
            ).strip()

            evidence = str(
                raw_item.get("evidence", "")
                or ""
            ).strip()

            category = str(
                raw_item.get("category", "")
                or ""
            ).strip()

            if not requirement:
                continue

            normalized_requirement = self._normalize_text(
                requirement
            )

            if (
                normalized_requirement
                not in normalized_vacancy
            ):
                continue

            if category not in allowed_categories:
                category = self._requirement_category(
                    requirement
                )

            evidence_missing = (
                not evidence
                or self._normalize_text(evidence)
                == self._normalize_text(
                    "Não evidenciado no currículo."
                )
            )

            if evidence_missing:
                evidence = "Não evidenciado no currículo."
                score = 0.0
            else:
                normalized_evidence = self._normalize_text(
                    evidence
                )

                if (
                    normalized_evidence
                    not in normalized_curriculum
                ):
                    evidence = "Não evidenciado no currículo."
                    score = 0.0
                else:
                    try:
                        score = float(
                            raw_item.get("score", 0.0)
                        )
                    except (TypeError, ValueError):
                        score = 0.0

                    score = round(
                        max(
                            0.0,
                            min(score, 100.0),
                        ),
                        1,
                    )

            validated.append(
                ResumeMatchRequirement(
                    category=category,
                    requirement=requirement,
                    evidence=evidence,
                    score=score,
                    status=self._requirement_status(
                        score
                    ),
                )
            )

        return tuple(validated)

    @staticmethod
    def _semantic_json_payload(
        raw: str,
    ) -> dict[str, object]:
        candidate = raw.strip()

        if candidate.startswith("```"):
            candidate = re.sub(
                r"^```(?:json)?\s*",
                "",
                candidate,
                flags=re.IGNORECASE,
            )
            candidate = re.sub(
                r"\s*```$",
                "",
                candidate,
            )

        payload = json.loads(candidate)

        if not isinstance(payload, dict):
            raise ValueError(
                "A análise semântica não retornou um objeto JSON."
            )

        return payload
    def get_cached(
        self,
        *,
        application: object,
        curriculum: object,
    ) -> ResumeMatchResult | None:
        vacancy_text = self._vacancy_text(application)
        curriculum_text = self._curriculum_text(curriculum)

        return self._load_cached(
            self._cache_key(
                application=application,
                curriculum=curriculum,
                vacancy_text=vacancy_text,
                curriculum_text=curriculum_text,
            )
        )

    def _calculate(
        self,
        *,
        vacancy_text: str,
        curriculum_text: str,
    ) -> ResumeMatchResult:
        vacancy_keywords = self._keywords(vacancy_text)
        curriculum_keywords = self._keywords(curriculum_text)

        matched = sorted(vacancy_keywords & curriculum_keywords)
        missing = sorted(vacancy_keywords - curriculum_keywords)

        if not vacancy_keywords:
            return self._empty_result()

        coverage = len(matched) / len(vacancy_keywords)

        technical_score = round(coverage * 100.0, 1)
        ats_score = round(
            min(99.0, 45.0 + (coverage * 54.0)),
            1,
        )

        optimization_gain = min(
            22.0,
            (100.0 - technical_score) * 0.72,
        )

        adapted_technical = round(
            min(99.0, technical_score + optimization_gain),
            1,
        )

        adapted_ats = round(
            min(
                99.0,
                ats_score + ((99.0 - ats_score) * 0.82),
            ),
            1,
        )

        current_min, current_max = self._probability_range(
            self._interview_estimate(
                ats_score=ats_score,
                technical_score=technical_score,
            )
        )

        adapted_min, adapted_max = self._probability_range(
            self._interview_estimate(
                ats_score=adapted_ats,
                technical_score=adapted_technical,
            )
        )

        requirements = self._build_requirements(
            vacancy_text=vacancy_text,
            curriculum_text=curriculum_text,
        )

        dimensions = self._build_dimension_scores(requirements)
        strengths = self._build_strengths(requirements)
        gaps = self._build_gaps(requirements)

        return ResumeMatchResult(
            score=technical_score,
            adapted_score=adapted_technical,
            ats_score=ats_score,
            adapted_ats_score=adapted_ats,
            interview_probability_min=current_min,
            interview_probability_max=current_max,
            adapted_interview_probability_min=adapted_min,
            adapted_interview_probability_max=adapted_max,
            matched_keywords=tuple(matched),
            missing_keywords=tuple(missing),
            requirements=requirements,
            dimension_scores=dimensions,
            strengths=strengths,
            gaps=gaps,
            differentials=self._build_differentials(
                vacancy_keywords=vacancy_keywords,
                curriculum_keywords=curriculum_keywords,
            ),
            recommendation=self._recommendation(technical_score),
            adaptation_strategy=self._build_adaptation_strategy(
                requirements=requirements,
                matched_keywords=tuple(matched),
            ),
            analyzed_at=datetime.now(UTC).isoformat(),
        )

    def _build_requirements(
        self,
        *,
        vacancy_text: str,
        curriculum_text: str,
    ) -> tuple[ResumeMatchRequirement, ...]:
        vacancy_segments = self._text_segments(vacancy_text)
        curriculum_segments = self._text_segments(curriculum_text)

        requirements: list[ResumeMatchRequirement] = []

        for requirement in vacancy_segments:
            requirement_keywords = self._keywords(requirement)

            if not requirement_keywords:
                continue

            evidence, score = self._best_evidence(
                requirement_keywords=requirement_keywords,
                curriculum_segments=curriculum_segments,
            )

            requirements.append(
                ResumeMatchRequirement(
                    category=self._requirement_category(requirement),
                    requirement=requirement,
                    evidence=evidence,
                    score=score,
                    status=self._requirement_status(score),
                )
            )

        if requirements:
            return tuple(requirements)

        return (
            ResumeMatchRequirement(
                category="Conhecimentos técnicos",
                requirement=vacancy_text.strip(),
                evidence="Não evidenciado no currículo.",
                score=0.0,
                status="Gap",
            ),
        )

    def _best_evidence(
        self,
        *,
        requirement_keywords: set[str],
        curriculum_segments: tuple[str, ...],
    ) -> tuple[str, float]:
        best_segment = ""
        best_score = 0.0
        best_matched_count = 0

        for segment in curriculum_segments:
            segment_keywords = self._keywords(segment)

            if not segment_keywords:
                continue

            matched_count = len(
                requirement_keywords & segment_keywords
            )

            if matched_count == 0:
                continue

            score = (
                matched_count
                / max(1, len(requirement_keywords))
                * 100.0
            )

            if (
                score > best_score
                or (
                    score == best_score
                    and matched_count > best_matched_count
                )
            ):
                best_score = score
                best_matched_count = matched_count
                best_segment = segment.strip()

        if not best_segment:
            return "Não evidenciado no currículo.", 0.0

        return best_segment, round(min(100.0, best_score), 1)

    def _build_dimension_scores(
        self,
        requirements: tuple[ResumeMatchRequirement, ...],
    ) -> tuple[ResumeMatchDimension, ...]:
        grouped: dict[str, list[float]] = {}

        for requirement in requirements:
            grouped.setdefault(
                requirement.category,
                [],
            ).append(requirement.score)

        return tuple(
            ResumeMatchDimension(
                name=category,
                score=round(
                    sum(scores) / len(scores),
                    1,
                ),
            )
            for category, scores in grouped.items()
        )

    def _build_strengths(
        self,
        requirements: tuple[ResumeMatchRequirement, ...],
    ) -> tuple[str, ...]:
        strong = sorted(
            (
                requirement
                for requirement in requirements
                if requirement.score >= 65
            ),
            key=lambda item: item.score,
            reverse=True,
        )

        return tuple(
            requirement.requirement
            for requirement in strong[:6]
        )

    def _build_gaps(
        self,
        requirements: tuple[ResumeMatchRequirement, ...],
    ) -> tuple[str, ...]:
        weak = sorted(
            (
                requirement
                for requirement in requirements
                if requirement.score < 40
            ),
            key=lambda item: item.score,
        )

        return tuple(
            requirement.requirement
            for requirement in weak[:6]
        )

    def _build_differentials(
        self,
        *,
        vacancy_keywords: set[str],
        curriculum_keywords: set[str],
    ) -> tuple[str, ...]:
        additional = sorted(
            curriculum_keywords - vacancy_keywords
        )

        if not additional:
            return ()

        grouped = ", ".join(additional[:8])

        return (
            f"Competências adicionais identificadas no currículo: {grouped}.",
        )

    def _build_adaptation_strategy(
        self,
        *,
        requirements: tuple[ResumeMatchRequirement, ...],
        matched_keywords: tuple[str, ...],
    ) -> tuple[str, ...]:
        strategies: list[str] = []

        strong_requirements = [
            requirement.requirement
            for requirement in requirements
            if requirement.score >= 65
        ]

        partial_requirements = [
            requirement.requirement
            for requirement in requirements
            if 20 <= requirement.score < 65
        ]

        missing_requirements = [
            requirement.requirement
            for requirement in requirements
            if requirement.score < 20
        ]

        if strong_requirements:
            strategies.append(
                "Priorizar no resumo profissional e nas experiências "
                "as competências já comprovadas que possuem maior "
                "aderência à vaga."
            )

        if matched_keywords:
            strategies.append(
                "Reforçar, de forma natural, as palavras-chave já "
                "comprovadas no currículo: "
                + ", ".join(matched_keywords[:10])
                + "."
            )

        if partial_requirements:
            strategies.append(
                "Revisar as experiências existentes para tornar mais "
                "explícitas as evidências verdadeiras relacionadas aos "
                "requisitos parcialmente atendidos."
            )

        if missing_requirements:
            strategies.append(
                "Não inserir como experiência ou conhecimento os "
                "requisitos sem evidência no currículo; mantê-los como "
                "gaps para decisão do candidato."
            )

        return tuple(strategies)

    def _recommendation(self, score: float) -> str:
        if score >= 90:
            return (
                "Aderência muito alta. A candidatura é fortemente "
                "recomendada; concentre a adaptação em posicionamento "
                "e palavras-chave."
            )

        if score >= 75:
            return (
                "Aderência alta. Recomenda-se a candidatura com adaptação "
                "direcionada do currículo para destacar os requisitos "
                "mais relevantes."
            )

        if score >= 60:
            return (
                "Aderência moderada. A candidatura é viável, mas o "
                "currículo deve evidenciar melhor as competências "
                "já existentes e os gaps devem ser avaliados."
            )

        if score >= 40:
            return (
                "Aderência baixa. Recomenda-se avaliar se os principais "
                "requisitos ausentes são eliminatórios antes da candidatura."
            )

        return (
            "Aderência muito baixa. Os requisitos principais da vaga não "
            "estão suficientemente evidenciados no currículo atual."
        )

    def _requirement_category(self, requirement: str) -> str:
        normalized = self._normalize_text(requirement)

        for category, terms in self._CATEGORY_PATTERNS:
            if any(term in normalized for term in terms):
                return category

        return "Conhecimentos técnicos"

    @staticmethod
    def _requirement_status(score: float) -> str:
        if score >= 85:
            return "Forte"

        if score >= 65:
            return "Aderente"

        if score >= 40:
            return "Parcial"

        if score > 0:
            return "Baixa evidência"

        return "Gap"

    def _cache_key(
        self,
        *,
        application: object,
        curriculum: object,
        vacancy_text: str,
        curriculum_text: str,
    ) -> str:
        application_id = getattr(application, "id", "")
        job = getattr(application, "job", None)
        job_id = getattr(
            job,
            "id",
            getattr(application, "job_id", ""),
        )
        curriculum_id = getattr(curriculum, "id", "")

        fingerprint = sha256(
            f"{vacancy_text}\0{curriculum_text}".encode()
        ).hexdigest()

        return (
            f"{self._CACHE_VERSION}:"
            f"{application_id}:"
            f"{job_id}:"
            f"{curriculum_id}:"
            f"{fingerprint}"
        )

    def _load_cached(
        self,
        cache_key: str,
    ) -> ResumeMatchResult | None:
        payload = self._read_cache().get(cache_key)

        if not isinstance(payload, dict):
            return None

        try:
            requirements = tuple(
                self._deserialize_requirement(item)
                for item in payload.get("requirements", ())
                if isinstance(item, dict)
            )

            dimensions = tuple(
                self._deserialize_dimension(item)
                for item in payload.get("dimension_scores", ())
                if isinstance(item, dict)
            )

            return ResumeMatchResult(
                score=float(payload["score"]),
                adapted_score=float(payload["adapted_score"]),
                ats_score=float(payload["ats_score"]),
                adapted_ats_score=float(
                    payload["adapted_ats_score"]
                ),
                interview_probability_min=float(
                    payload["interview_probability_min"]
                ),
                interview_probability_max=float(
                    payload["interview_probability_max"]
                ),
                adapted_interview_probability_min=float(
                    payload[
                        "adapted_interview_probability_min"
                    ]
                ),
                adapted_interview_probability_max=float(
                    payload[
                        "adapted_interview_probability_max"
                    ]
                ),
                matched_keywords=tuple(
                    payload.get("matched_keywords", ())
                ),
                missing_keywords=tuple(
                    payload.get("missing_keywords", ())
                ),
                requirements=requirements,
                dimension_scores=dimensions,
                strengths=tuple(
                    payload.get("strengths", ())
                ),
                gaps=tuple(payload.get("gaps", ())),
                differentials=tuple(
                    payload.get("differentials", ())
                ),
                recommendation=str(
                    payload.get("recommendation", "")
                ),
                adaptation_strategy=tuple(
                    payload.get("adaptation_strategy", ())
                ),
                analyzed_at=str(
                    payload.get("analyzed_at", "")
                ),
            )

        except (KeyError, TypeError, ValueError):
            return None

    @staticmethod
    def _deserialize_requirement(
        payload: dict[str, object],
    ) -> ResumeMatchRequirement:
        return ResumeMatchRequirement(
            category=str(payload.get("category", "")),
            requirement=str(
                payload.get("requirement", "")
            ),
            evidence=str(payload.get("evidence", "")),
            score=float(payload.get("score", 0.0)),
            status=str(payload.get("status", "")),
        )

    @staticmethod
    def _deserialize_dimension(
        payload: dict[str, object],
    ) -> ResumeMatchDimension:
        return ResumeMatchDimension(
            name=str(payload.get("name", "")),
            score=float(payload.get("score", 0.0)),
        )

    def _save_cached(
        self,
        cache_key: str,
        result: ResumeMatchResult,
    ) -> None:
        data = self._read_cache()
        payload = asdict(result)

        payload["matched_keywords"] = list(
            result.matched_keywords
        )
        payload["missing_keywords"] = list(
            result.missing_keywords
        )
        payload["strengths"] = list(result.strengths)
        payload["gaps"] = list(result.gaps)
        payload["differentials"] = list(
            result.differentials
        )
        payload["adaptation_strategy"] = list(
            result.adaptation_strategy
        )

        data[cache_key] = payload

        self.storage_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary = self.storage_path.with_suffix(
            ".tmp"
        )

        temporary.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        temporary.replace(self.storage_path)

    def _read_cache(self) -> dict[str, object]:
        if not self.storage_path.exists():
            return {}

        try:
            loaded = json.loads(
                self.storage_path.read_text(
                    encoding="utf-8"
                )
            )
        except (
            OSError,
            ValueError,
            json.JSONDecodeError,
        ):
            return {}

        return (
            loaded
            if isinstance(loaded, dict)
            else {}
        )

    def _vacancy_text(
        self,
        application: object,
    ) -> str:
        job = getattr(application, "job", None)

        return str(
            getattr(job, "notes", "") or ""
        ).strip()

    def _curriculum_text(
        self,
        curriculum: object,
    ) -> str:
        values = [
            str(
                getattr(curriculum, "name", "")
                or ""
            ),
            str(
                getattr(curriculum, "description", "")
                or ""
            ),
            str(
                getattr(curriculum, "language", "")
                or ""
            ),
        ]

        structured = getattr(
            curriculum,
            "structured_content_json",
            None,
        )

        if structured:
            try:
                decoded = json.loads(structured)
            except (
                TypeError,
                ValueError,
                json.JSONDecodeError,
            ):
                values.append(str(structured))
            else:
                values.append(
                    json.dumps(
                        decoded,
                        ensure_ascii=False,
                    )
                )

        return " ".join(values)

    def _keywords(self, text: str) -> set[str]:
        normalized = self._normalize_text(text)

        words = re.findall(
            r"[a-z0-9][a-z0-9+#./-]{2,}",
            normalized,
        )

        return {
            word.strip("./-")
            for word in words
            if (
                word not in self._STOP_WORDS
                and len(word.strip("./-")) >= 3
            )
        }

    def _text_segments(
        self,
        text: str,
    ) -> tuple[str, ...]:
        cleaned = text.replace("\r\n", "\n").replace(
            "\r",
            "\n",
        )

        parts = re.split(
            r"""
            (?:\n+\s*)
            |
            (?<=[.!?;])\s+
            |
            (?:\s+[•▪●◦]\s*)
            """,
            cleaned,
            flags=re.VERBOSE,
        )

        segments: list[str] = []

        for part in parts:
            normalized = re.sub(
                r"^\s*(?:[-–—*•▪●◦✓✔]+\s*)+",
                "",
                part,
            ).strip()

            if len(normalized) < 3:
                continue

            segments.append(normalized)

        return tuple(dict.fromkeys(segments))

    @staticmethod
    def _normalize_text(text: str) -> str:
        normalized = unicodedata.normalize(
            "NFKD",
            text.casefold(),
        )

        return "".join(
            char
            for char in normalized
            if not unicodedata.combining(char)
        )

    def _interview_estimate(
        self,
        *,
        ats_score: float,
        technical_score: float,
    ) -> float:
        return min(
            97.0,
            (ats_score * 0.42)
            + (technical_score * 0.48),
        )

    @staticmethod
    def _probability_range(
        center: float,
    ) -> tuple[float, float]:
        return (
            max(0.0, round(center - 2.0, 1)),
            min(97.0, round(center + 2.0, 1)),
        )

    def _empty_result(self) -> ResumeMatchResult:
        return ResumeMatchResult(
            score=0.0,
            adapted_score=0.0,
            ats_score=0.0,
            adapted_ats_score=0.0,
            interview_probability_min=0.0,
            interview_probability_max=0.0,
            adapted_interview_probability_min=0.0,
            adapted_interview_probability_max=0.0,
            matched_keywords=(),
            missing_keywords=(),
            requirements=(),
            dimension_scores=(),
            strengths=(),
            gaps=(),
            differentials=(),
            recommendation="",
            adaptation_strategy=(),
        )
