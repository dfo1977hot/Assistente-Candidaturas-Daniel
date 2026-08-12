from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path
import re
import unicodedata


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
    analyzed_at: str = ""

    @property
    def has_vacancy_description(self) -> bool:
        return bool(self.matched_keywords or self.missing_keywords)


class ResumeMatchService:
    """Compara currículo e vaga, persistindo resultados reutilizáveis."""

    _STOP_WORDS = {
        "a", "ao", "aos", "as", "com", "como", "da", "das", "de", "do", "dos",
        "e", "em", "entre", "na", "nas", "no", "nos", "o", "os", "ou", "para",
        "por", "que", "se", "ser", "sua", "suas", "seu", "seus", "um", "uma",
        "the", "and", "for", "with", "from", "this", "that", "will", "you",
    }

    def __init__(self, storage_path: str | Path = "data/resume_match_results.json") -> None:
        self.storage_path = Path(storage_path)

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

        result = self._calculate(vacancy_text=vacancy_text, curriculum_text=curriculum_text)
        if result.has_vacancy_description:
            self._save_cached(cache_key, result)
        return result

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

    def _calculate(self, *, vacancy_text: str, curriculum_text: str) -> ResumeMatchResult:
        vacancy_keywords = self._keywords(vacancy_text)
        curriculum_keywords = self._keywords(curriculum_text)
        matched = sorted(vacancy_keywords & curriculum_keywords)
        missing = sorted(vacancy_keywords - curriculum_keywords)
        if not vacancy_keywords:
            return self._empty_result()

        coverage = len(matched) / len(vacancy_keywords)
        technical_score = round(coverage * 100.0, 1)
        ats_score = round(min(99.0, 45.0 + (coverage * 54.0)), 1)
        optimization_gain = min(22.0, (100.0 - technical_score) * 0.72)
        adapted_technical = round(min(99.0, technical_score + optimization_gain), 1)
        adapted_ats = round(min(99.0, ats_score + ((99.0 - ats_score) * 0.82)), 1)

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
            analyzed_at=datetime.now(UTC).isoformat(),
        )

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
        job_id = getattr(job, "id", getattr(application, "job_id", ""))
        curriculum_id = getattr(curriculum, "id", "")
        fingerprint = sha256(
            f"{vacancy_text}\0{curriculum_text}".encode()
        ).hexdigest()
        return f"{application_id}:{job_id}:{curriculum_id}:{fingerprint}"

    def _load_cached(self, cache_key: str) -> ResumeMatchResult | None:
        payload = self._read_cache().get(cache_key)
        if not isinstance(payload, dict):
            return None
        try:
            return ResumeMatchResult(
                score=float(payload["score"]),
                adapted_score=float(payload["adapted_score"]),
                ats_score=float(payload["ats_score"]),
                adapted_ats_score=float(payload["adapted_ats_score"]),
                interview_probability_min=float(payload["interview_probability_min"]),
                interview_probability_max=float(payload["interview_probability_max"]),
                adapted_interview_probability_min=float(
                    payload["adapted_interview_probability_min"]
                ),
                adapted_interview_probability_max=float(
                    payload["adapted_interview_probability_max"]
                ),
                matched_keywords=tuple(payload.get("matched_keywords", ())),
                missing_keywords=tuple(payload.get("missing_keywords", ())),
                analyzed_at=str(payload.get("analyzed_at", "")),
            )
        except (KeyError, TypeError, ValueError):
            return None

    def _save_cached(self, cache_key: str, result: ResumeMatchResult) -> None:
        data = self._read_cache()
        payload = asdict(result)
        payload["matched_keywords"] = list(result.matched_keywords)
        payload["missing_keywords"] = list(result.missing_keywords)
        data[cache_key] = payload
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.storage_path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(self.storage_path)

    def _read_cache(self) -> dict[str, object]:
        if not self.storage_path.exists():
            return {}
        try:
            loaded = json.loads(self.storage_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            return {}
        return loaded if isinstance(loaded, dict) else {}

    def _vacancy_text(self, application: object) -> str:
        job = getattr(application, "job", None)
        return str(getattr(job, "notes", "") or "").strip()

    def _curriculum_text(self, curriculum: object) -> str:
        values = [
            str(getattr(curriculum, "name", "") or ""),
            str(getattr(curriculum, "description", "") or ""),
            str(getattr(curriculum, "language", "") or ""),
        ]
        structured = getattr(curriculum, "structured_content_json", None)
        if structured:
            try:
                decoded = json.loads(structured)
            except (TypeError, ValueError, json.JSONDecodeError):
                values.append(str(structured))
            else:
                values.append(json.dumps(decoded, ensure_ascii=False))
        return " ".join(values)

    def _keywords(self, text: str) -> set[str]:
        normalized = unicodedata.normalize("NFKD", text.casefold())
        normalized = "".join(char for char in normalized if not unicodedata.combining(char))
        words = re.findall(r"[a-z0-9][a-z0-9+#./-]{2,}", normalized)
        return {
            word.strip("./-")
            for word in words
            if word not in self._STOP_WORDS and len(word.strip("./-")) >= 3
        }

    def _interview_estimate(self, *, ats_score: float, technical_score: float) -> float:
        return min(97.0, (ats_score * 0.42) + (technical_score * 0.48))

    def _probability_range(self, center: float) -> tuple[float, float]:
        return max(0.0, round(center - 2.0, 1)), min(97.0, round(center + 2.0, 1))

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
            matched_keywords=tuple(),
            missing_keywords=tuple(),
        )
