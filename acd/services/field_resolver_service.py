from __future__ import annotations

from collections.abc import Iterable
import re


class FieldResolverService:
    """Resolve automaticamente o melhor campo do perfil para um campo alvo da plataforma."""

    def resolve(self, source_field: str, candidates: Iterable[str]) -> str | None:
        normalized_source = self._normalize(source_field)
        best_candidate: str | None = None
        best_score = -1
        for candidate in candidates:
            score = self._score(normalized_source, self._normalize(candidate))
            if score > best_score:
                best_score = score
                best_candidate = candidate
        return best_candidate

    def _score(self, source: str, candidate: str) -> int:
        if source == candidate:
            return 100
        if source in candidate or candidate in source:
            return 60
        if re.search(rf"{re.escape(source[:3])}", candidate):
            return 30
        return 0

    def _normalize(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", value.lower())
