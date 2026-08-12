from __future__ import annotations

from types import SimpleNamespace

from acd.presentation.models.resume_optimization_view_state import ResumeOptimizationViewState
from acd.presentation.pages.application_page import ApplicationPage
from acd.presentation.pages.curriculum_page import CurriculumPage


class _Repository:
    def __init__(self, curricula):
        self._curricula = curricula

    def get_all(self):
        return list(self._curricula)

    def get_by_id(self, curriculum_id):
        return next((item for item in self._curricula if item.id == curriculum_id), None)


class _CurriculumPageService:
    def __init__(self, curricula):
        self.repository = _Repository(curricula)


def _curriculum(curriculum_id: int, version: str):
    return SimpleNamespace(
        id=curriculum_id,
        name="Currículo Logística",
        version=version,
        language="pt-BR",
        description=f"Conteúdo {version}",
        file_original_name=None,
        file_relative_path=None,
        file_extension=None,
        is_default=False,
    )


def test_curriculum_page_opens_newly_created_curriculum(qapp) -> None:
    original = _curriculum(1, "V.1.0")
    optimized = _curriculum(2, "V.1.1")
    page = CurriculumPage(_CurriculumPageService([original, optimized]))  # type: ignore[arg-type]

    assert page.open_curriculum(optimized.id)

    assert page.current_curriculum_id == optimized.id
    assert page.version_input.text() == "V.1.1"
    assert page.description_input.toPlainText() == "Conteúdo V.1.1"


def test_application_page_notifies_created_curriculum(qapp, monkeypatch) -> None:
    optimized = _curriculum(2, "V.1.1")
    opened: list[int] = []
    service = SimpleNamespace(
        list_curricula=lambda: [optimized],
        associate_to_application=lambda **_: SimpleNamespace(id=42),
    )
    page = ApplicationPage(
        on_optimized_curriculum_created=opened.append,
        curriculum_service=service,  # type: ignore[arg-type]
    )
    page.current_application_id = 42
    page._optimization_source_curriculum_id = 1
    monkeypatch.setattr(page, "refresh_reference_data", lambda: None)

    state = ResumeOptimizationViewState(
        42,
        "success",
        "Currículo otimizado",
        "Nova versão criada.",
        True,
        "v2.0",
    )
    page._on_optimization_succeeded((state, optimized))

    assert opened == [2]
    assert page.curriculum_combo.currentData() == 2
    assert "V.1.1" in page.optimization_status_label.text()
