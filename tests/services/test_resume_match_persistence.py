from __future__ import annotations

from types import SimpleNamespace

from acd.services.resume_match_service import ResumeMatchService


def _application() -> SimpleNamespace:
    return SimpleNamespace(
        id=10,
        job_id=20,
        job=SimpleNamespace(id=20, notes="Python SQL logística Power BI"),
    )


def _curriculum(description: str = "Python e SQL") -> SimpleNamespace:
    return SimpleNamespace(
        id=30,
        name="Analista",
        description=description,
        language="pt-BR",
        structured_content_json=None,
    )


def test_resume_match_is_persisted_and_reused(tmp_path) -> None:
    storage = tmp_path / "resume_match_results.json"
    service = ResumeMatchService(storage)

    first = service.analyze(
        application=_application(),
        curriculum=_curriculum(),
    )
    second = ResumeMatchService(storage).get_cached(
        application=_application(),
        curriculum=_curriculum(),
    )

    assert storage.exists()
    assert second == first


def test_resume_match_cache_is_invalidated_when_curriculum_changes(tmp_path) -> None:
    service = ResumeMatchService(tmp_path / "resume_match_results.json")
    application = _application()

    original = service.analyze(
        application=application,
        curriculum=_curriculum("Python e SQL"),
    )
    changed = service.get_cached(
        application=application,
        curriculum=_curriculum("Python SQL logística Power BI"),
    )

    assert original.has_vacancy_description
    assert changed is None
