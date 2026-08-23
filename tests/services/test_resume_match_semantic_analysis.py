from __future__ import annotations

import json
from types import SimpleNamespace

from acd.services.resume_match_service import ResumeMatchService


class _AIProvider:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.calls = 0

    def generate_text(
        self,
        *,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        language: str,
        web_search: bool = False,
    ) -> str:
        del prompt
        del model
        del temperature
        del max_tokens
        del language
        del web_search

        self.calls += 1
        return json.dumps(
            self.payload,
            ensure_ascii=False,
        )


class _FailingAIProvider:
    def generate_text(
        self,
        *,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        language: str,
        web_search: bool = False,
    ) -> str:
        del prompt
        del model
        del temperature
        del max_tokens
        del language
        del web_search

        raise RuntimeError("IA indisponível")


def _application(notes: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=1,
        job_id=10,
        job=SimpleNamespace(
            id=10,
            notes=notes,
        ),
    )


def _curriculum(description: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=20,
        name="Currículo",
        description=description,
        language="pt-BR",
        structured_content_json=None,
    )


def test_semantic_analysis_uses_validated_evidence(
    tmp_path,
) -> None:
    vacancy = (
        "Experiência com Lean Six Sigma. "
        "Conhecimento em SAP QM."
    )
    curriculum_text = (
        "Green Belt Lean Six Sigma. "
        "Experiência com SAP MM, PP e SD."
    )

    provider = _AIProvider(
        {
            "requirements": [
                {
                    "category": "Metodologias / Qualidade",
                    "requirement": "Experiência com Lean Six Sigma.",
                    "evidence": "Green Belt Lean Six Sigma.",
                    "score": 95,
                },
                {
                    "category": "Sistemas e ferramentas",
                    "requirement": "Conhecimento em SAP QM.",
                    "evidence": "Experiência com SAP MM, PP e SD.",
                    "score": 45,
                },
            ]
        }
    )

    service = ResumeMatchService(
        storage_path=tmp_path / "cache.json",
        ai_provider=provider,
    )

    result = service.analyze_semantic(
        application=_application(vacancy),
        curriculum=_curriculum(curriculum_text),
    )

    assert provider.calls == 1
    assert len(result.requirements) == 2
    assert result.requirements[0].score == 95
    assert result.requirements[0].status == "Forte"
    assert result.requirements[1].score == 45
    assert result.requirements[1].status == "Parcial"
    assert result.requirements[1].evidence == (
        "Experiência com SAP MM, PP e SD."
    )
    assert result.score == 70.0


def test_semantic_analysis_rejects_invented_evidence(
    tmp_path,
) -> None:
    provider = _AIProvider(
        {
            "requirements": [
                {
                    "category": "Sistemas e ferramentas",
                    "requirement": "Conhecimento em SAP QM.",
                    "evidence": "Experiência avançada em SAP QM.",
                    "score": 100,
                }
            ]
        }
    )

    service = ResumeMatchService(
        storage_path=tmp_path / "cache.json",
        ai_provider=provider,
    )

    result = service.analyze_semantic(
        application=_application(
            "Conhecimento em SAP QM."
        ),
        curriculum=_curriculum(
            "Experiência com SAP MM, PP e SD."
        ),
    )

    requirement = result.requirements[0]

    assert requirement.evidence == (
        "Não evidenciado no currículo."
    )
    assert requirement.score == 0
    assert requirement.status == "Gap"


def test_semantic_analysis_rejects_invented_requirement(
    tmp_path,
) -> None:
    provider = _AIProvider(
        {
            "requirements": [
                {
                    "category": "Sistemas e ferramentas",
                    "requirement": "Experiência com Oracle Cloud.",
                    "evidence": "Experiência com Oracle TMS.",
                    "score": 60,
                }
            ]
        }
    )

    service = ResumeMatchService(
        storage_path=tmp_path / "cache.json",
        ai_provider=provider,
    )

    application = _application(
        "Conhecimento em SAP."
    )
    curriculum = _curriculum(
        "Experiência com Oracle TMS."
    )

    deterministic = service.analyze(
        application=application,
        curriculum=curriculum,
    )

    result = service.analyze_semantic(
        application=application,
        curriculum=curriculum,
        force=True,
    )

    assert result.score == deterministic.score


def test_semantic_analysis_falls_back_when_ai_fails(
    tmp_path,
) -> None:
    service = ResumeMatchService(
        storage_path=tmp_path / "cache.json",
        ai_provider=_FailingAIProvider(),
    )

    application = _application(
        "Logística transportes indicadores SAP."
    )
    curriculum = _curriculum(
        "Logística transportes indicadores."
    )

    deterministic = service.analyze(
        application=application,
        curriculum=curriculum,
    )

    semantic = service.analyze_semantic(
        application=application,
        curriculum=curriculum,
        force=True,
    )

    assert semantic.score == deterministic.score
    assert semantic.ats_score == deterministic.ats_score
    assert (
        semantic.matched_keywords
        == deterministic.matched_keywords
    )


def test_semantic_analysis_reuses_cache(
    tmp_path,
) -> None:
    provider = _AIProvider(
        {
            "requirements": [
                {
                    "category": "Experiência",
                    "requirement": "Experiência em logística.",
                    "evidence": "Experiência em logística.",
                    "score": 100,
                }
            ]
        }
    )

    service = ResumeMatchService(
        storage_path=tmp_path / "cache.json",
        ai_provider=provider,
    )

    application = _application(
        "Experiência em logística."
    )
    curriculum = _curriculum(
        "Experiência em logística."
    )

    first = service.analyze_semantic(
        application=application,
        curriculum=curriculum,
    )

    second = service.analyze_semantic(
        application=application,
        curriculum=curriculum,
    )

    assert first == second
    assert provider.calls == 1