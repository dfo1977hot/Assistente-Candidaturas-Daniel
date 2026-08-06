from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from difflib import SequenceMatcher
import re
import unicodedata

_IGNORED_TOKENS = {
    "a",
    "as",
    "da",
    "das",
    "de",
    "do",
    "dos",
    "e",
    "ltda",
    "me",
    "sa",
    "s",
}


@dataclass(frozen=True, slots=True)
class CompanyNameCandidate:
    index: int
    name: str
    score: float
    exact: bool


def normalize_company_name(value: str) -> str:
    """Normaliza nomes comerciais e razões sociais para comparação."""
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    ascii_text = "".join(char for char in decomposed if not unicodedata.combining(char))
    tokens = re.findall(r"[a-z0-9]+", ascii_text)
    meaningful = [token for token in tokens if token not in _IGNORED_TOKENS]
    return " ".join(meaningful)


def find_company_name_candidate(
    imported_name: str,
    candidates: Iterable[tuple[int, str]],
    *,
    minimum_score: float = 0.88,
) -> CompanyNameCandidate | None:
    """Encontra a melhor empresa cadastrada para um nome importado."""
    imported_literal = imported_name.strip().casefold()
    imported_normalized = normalize_company_name(imported_name)
    if not imported_normalized:
        return None

    best: CompanyNameCandidate | None = None
    for index, candidate_name in candidates:
        candidate_literal = candidate_name.strip().casefold()
        candidate_normalized = normalize_company_name(candidate_name)
        if not candidate_normalized:
            continue

        if candidate_literal == imported_literal:
            return CompanyNameCandidate(index, candidate_name, 1.0, True)

        if candidate_normalized == imported_normalized:
            score = 1.0
        else:
            score = SequenceMatcher(
                None,
                imported_normalized,
                candidate_normalized,
            ).ratio()

        candidate = CompanyNameCandidate(index, candidate_name, score, False)
        if best is None or candidate.score > best.score:
            best = candidate

    if best is None or best.score < minimum_score:
        return None
    return best
