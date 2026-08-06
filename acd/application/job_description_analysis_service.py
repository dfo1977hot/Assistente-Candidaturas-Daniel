"""Application service for initial job-description analysis."""

from __future__ import annotations

from collections import Counter
import re

from acd.application.job_analysis_result import (
    JobAnalysisResult,
)


class JobAnalysisService:
    """
    Serviço responsável pela análise inicial de uma vaga.

    Esta primeira implementação utiliza apenas regras simples.
    Futuramente poderá ser substituída por IA sem alterar a API.
    """

    _SENIOR_KEYWORDS = {
        "senior",
        "sênior",
        "especialista",
        "especialista(a)",
        "coordenador",
        "coordenadora",
        "gerente",
        "manager",
        "lead",
        "líder",
        "lider",
        "head",
        "director",
        "diretor",
    }

    _PLENO_KEYWORDS = {
        "pleno",
        "analista",
        "engineer",
        "engenheiro",
        "consultor",
    }

    def analyze(
        self,
        description: str,
    ) -> JobAnalysisResult:
        """
        Executa uma análise básica da descrição da vaga.
        """

        words = self._tokenize(description)

        unique_words = len(set(words))

        return JobAnalysisResult(
            total_words=len(words),
            unique_words=unique_words,
            estimated_level=self._estimate_level(words),
        )

    def keyword_frequency(
        self,
        description: str,
    ) -> Counter[str]:
        """
        Retorna a frequência das palavras da descrição.
        """

        return Counter(
            self._tokenize(description)
        )

    def _tokenize(
        self,
        text: str,
    ) -> list[str]:
        return re.findall(
            r"\b[\wÀ-ÿ]+\b",
            text.lower(),
        )

    def _estimate_level(
        self,
        words: list[str],
    ) -> str:
        vocabulary = set(words)

        if vocabulary & self._SENIOR_KEYWORDS:
            return "Senior"

        if vocabulary & self._PLENO_KEYWORDS:
            return "Pleno"

        return "Junior"
