from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from PySide6.QtWidgets import QFileDialog, QMessageBox

from acd.presentation.pages.curriculum_page import (
    CurriculumPage,
    _is_integrity_error,
)
from acd.services.curriculum_document_service import CurriculumDocumentError


class _IntegrityResult:
    def __init__(self, message: str = "Íntegro") -> None:
        self.message = message


class _DocumentService:
    def __init__(self) -> None:
        self.verified = []

    def verify_integrity(self, curriculum):
        self.verified.append(curriculum)
        return _IntegrityResult("Íntegro")


class _Repository:
    def __init__(self, curriculum) -> None:
        self.curriculum = curriculum

    def get_all(self):
        return [self.curriculum]

    def get_by_id(self, curriculum_id: int):
        if curriculum_id == self.curriculum.id:
            return self.curriculum
        return None


class _CurriculumService:
    def __init__(self) -> None:
        self.curriculum = SimpleNamespace(
            id=1,
            name="Currículo Principal",
            version="v2.0",
            language="pt-BR",
            description="Currículo para logística.",
            file_relative_path="curriculos/cv.docx",
            file_original_name="Daniel_CV.docx",
            file_extension=".docx",
            file_size_bytes=2048,
            is_default=True,
        )

        self.repository = _Repository(self.curriculum)
        self.document_service = _DocumentService()

        self.created: list[dict[str, object]] = []
        self.updated: list[tuple[int, dict[str, object]]] = []
        self.attached: list[tuple[int, Path]] = []
        self.opened: list[int] = []
        self.removed: list[int] = []
        self.duplicated: list[int] = []
        self.activated: list[int] = []
        self.deleted: list[tuple[int, bool]] = []
        self.search_queries: list[str] = []

        self.create_result = self.curriculum
        self.update_result = self.curriculum
        self.delete_outcomes: list[object] = []

        self.open_error: Exception | None = None
        self.remove_error: Exception | None = None
        self.attach_error: Exception | None = None

    def create_curriculum(self, **payload):
        self.created.append(dict(payload))
        return self.create_result

    def update_curriculum(
        self,
        curriculum_id: int,
        **payload,
    ):
        self.updated.append(
            (
                curriculum_id,
                dict(payload),
            )
        )
        return self.update_result

    def attach_document(
        self,
        curriculum_id: int,
        path: Path,
    ):
        if self.attach_error is not None:
            raise self.attach_error

        self.attached.append(
            (
                curriculum_id,
                path,
            )
        )

    def open_document(self, curriculum_id: int):
        if self.open_error is not None:
            raise self.open_error

        self.opened.append(curriculum_id)

    def remove_document(self, curriculum_id: int):
        if self.remove_error is not None:
            raise self.remove_error

        self.removed.append(curriculum_id)

    def duplicate_curriculum(self, curriculum_id: int):
        self.duplicated.append(curriculum_id)
        return self.curriculum

    def activate_curriculum(self, curriculum_id: int):
        self.activated.append(curriculum_id)

    def delete_curriculum(
        self,
        curriculum_id: int,
        *,
        delete_linked: bool = False,
    ):
        self.deleted.append(
            (
                curriculum_id,
                delete_linked,
            )
        )

        if self.delete_outcomes:
            outcome = self.delete_outcomes.pop(0)

            if isinstance(outcome, BaseException):
                raise outcome

            return outcome

        return True

    def search_curricula(self, query: str):
        self.search_queries.append(query)
        return [self.curriculum]


class IntegrityError(Exception):
    pass


def _page():
    service = _CurriculumService()

    page = CurriculumPage(
        service,  # type: ignore[arg-type]
    )

    return page, service


def _fill_form(page: CurriculumPage) -> None:
    page.name_input.setText("Currículo Logística")
    page.version_input.setText("v3.0")
    page.language_input.setText("pt-BR")
    page.description_input.setPlainText(
        "Currículo direcionado para logística."
    )


def test_initial_load_renders_curriculum(qapp) -> None:
    page, _service = _page()

    assert page.table.rowCount() == 1
    assert page.table.item(0, 0).text() == "1"
    assert page.table.item(0, 1).text() == "Currículo Principal"
    assert page.table.item(0, 2).text() == "v2.0"
    assert page.table.item(0, 3).text() == "pt-BR"
    assert page.table.item(0, 4).text() == "Daniel_CV.docx"
    assert page.table.item(0, 5).text() == "Sim"


def test_save_curriculum_requires_name(
    qapp,
    monkeypatch,
) -> None:
    page, service = _page()

    warnings: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: warnings.append(
            str(message)
        ),
    )

    page.name_input.clear()
    page._save_curriculum()

    assert service.created == []
    assert warnings == [
        "Informe o nome do currículo."
    ]


def test_save_curriculum_creates_with_defaults(
    qapp,
) -> None:
    page, service = _page()

    page.name_input.setText("Currículo Novo")
    page.version_input.clear()
    page.language_input.clear()
    page.description_input.setPlainText("Descrição")

    page.current_curriculum_id = None

    page._save_curriculum()

    assert len(service.created) == 1

    payload = service.created[0]

    assert payload == {
        "name": "Currículo Novo",
        "version": "v1.0",
        "language": "pt-BR",
        "description": "Descrição",
    }


def test_save_curriculum_updates_existing_record(
    qapp,
) -> None:
    page, service = _page()

    _fill_form(page)

    page.current_curriculum_id = 1

    page._save_curriculum()

    assert len(service.updated) == 1

    curriculum_id, payload = service.updated[0]

    assert curriculum_id == 1
    assert payload["name"] == "Currículo Logística"
    assert payload["version"] == "v3.0"


def test_save_curriculum_handles_missing_update(
    qapp,
    monkeypatch,
) -> None:
    page, service = _page()

    _fill_form(page)

    page.current_curriculum_id = 1
    service.update_result = None

    warnings: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: warnings.append(
            str(message)
        ),
    )

    page._save_curriculum()

    assert warnings == [
        "Currículo não encontrado."
    ]


def test_save_curriculum_attaches_pending_document(
    qapp,
    tmp_path,
) -> None:
    page, service = _page()

    _fill_form(page)

    selected = tmp_path / "curriculo.docx"
    selected.write_text("conteúdo", encoding="utf-8")

    page.pending_file_path = selected
    page.current_curriculum_id = None

    page._save_curriculum()

    assert service.attached == [
        (
            1,
            selected,
        )
    ]


def test_save_curriculum_handles_document_error(
    qapp,
    monkeypatch,
    tmp_path,
) -> None:
    page, service = _page()

    _fill_form(page)

    selected = tmp_path / "curriculo.docx"
    selected.write_text("conteúdo", encoding="utf-8")

    page.pending_file_path = selected

    service.attach_error = CurriculumDocumentError(
        "Falha no documento"
    )

    warnings: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: warnings.append(
            str(message)
        ),
    )

    page._save_curriculum()

    assert warnings == [
        "Falha no documento"
    ]


def test_select_file_can_be_cancelled(
    qapp,
    monkeypatch,
) -> None:
    page, _service = _page()

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *_args, **_kwargs: ("", ""),
    )

    page._select_file()

    assert page.pending_file_path is None


def test_select_file_rejects_invalid_extension(
    qapp,
    monkeypatch,
    tmp_path,
) -> None:
    page, _service = _page()

    selected = tmp_path / "arquivo.txt"

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *_args, **_kwargs: (
            str(selected),
            "",
        ),
    )

    warnings: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: warnings.append(
            str(message)
        ),
    )

    page._select_file()

    assert page.pending_file_path is None
    assert warnings == [
        "Selecione um arquivo DOCX ou PDF."
    ]


def test_select_file_accepts_docx(
    qapp,
    monkeypatch,
    tmp_path,
) -> None:
    page, _service = _page()

    selected = tmp_path / "curriculo.docx"

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *_args, **_kwargs: (
            str(selected),
            "",
        ),
    )

    page._select_file()

    assert page.pending_file_path == selected
    assert page.file_name_label.text() == "curriculo.docx"
    assert page.file_integrity_label.text() == "Pendente"
    assert not page.select_file_button.isEnabled()
    assert page.replace_file_button.isEnabled()


def test_open_file_requires_current_record(qapp) -> None:
    page, service = _page()

    page.current_curriculum_id = None

    page._open_file()

    assert service.opened == []


def test_open_file_calls_service(qapp) -> None:
    page, service = _page()

    page.current_curriculum_id = 1

    page._open_file()

    assert service.opened == [1]


def test_open_file_handles_document_error(
    qapp,
    monkeypatch,
) -> None:
    page, service = _page()

    page.current_curriculum_id = 1

    service.open_error = CurriculumDocumentError(
        "Arquivo indisponível"
    )

    warnings: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: warnings.append(
            str(message)
        ),
    )

    page._open_file()

    assert warnings == [
        "Arquivo indisponível"
    ]


def test_remove_pending_file_without_saved_record(
    qapp,
) -> None:
    page, _service = _page()

    page.current_curriculum_id = None
    page.pending_file_path = Path("curriculo.docx")

    page._remove_file()

    assert page.pending_file_path is None
    assert (
        page.file_name_label.text()
        == "Nenhum arquivo anexado"
    )


def test_remove_saved_file_can_be_cancelled(
    qapp,
    monkeypatch,
) -> None:
    page, service = _page()

    page.current_curriculum_id = 1

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.No,
    )

    page._remove_file()

    assert service.removed == []


def test_remove_saved_file_success(
    qapp,
    monkeypatch,
) -> None:
    page, service = _page()

    page.current_curriculum_id = 1

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.Yes,
    )

    page._remove_file()

    assert service.removed == [1]
    assert (
        page.file_name_label.text()
        == "Nenhum arquivo anexado"
    )


def test_remove_saved_file_handles_error(
    qapp,
    monkeypatch,
) -> None:
    page, service = _page()

    page.current_curriculum_id = 1
    service.remove_error = CurriculumDocumentError(
        "Falha ao remover"
    )

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.Yes,
    )

    warnings: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: warnings.append(
            str(message)
        ),
    )

    page._remove_file()

    assert warnings == [
        "Falha ao remover"
    ]


def test_duplicate_requires_selection(
    qapp,
    monkeypatch,
) -> None:
    page, service = _page()

    page.current_curriculum_id = None

    infos: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda _parent, _title, message: infos.append(
            str(message)
        ),
    )

    page._duplicate_curriculum()

    assert service.duplicated == []
    assert infos == [
        "Selecione um currículo."
    ]


def test_duplicate_curriculum_success(qapp) -> None:
    page, service = _page()

    page.current_curriculum_id = 1

    page._duplicate_curriculum()

    assert service.duplicated == [1]
    assert page.current_curriculum_id is None


def test_activate_curriculum_success(qapp) -> None:
    page, service = _page()

    page.current_curriculum_id = 1

    page._activate_curriculum()

    assert service.activated == [1]


def test_activate_curriculum_without_selection_does_nothing(
    qapp,
) -> None:
    page, service = _page()

    page.current_curriculum_id = None

    page._activate_curriculum()

    assert service.activated == []


def test_row_selection_populates_curriculum_and_document(
    qapp,
) -> None:
    page, service = _page()

    page.table.selectRow(0)

    assert page.current_curriculum_id == 1
    assert page.name_input.text() == "Currículo Principal"
    assert page.version_input.text() == "v2.0"
    assert page.language_input.text() == "pt-BR"
    assert (
        page.description_input.toPlainText()
        == "Currículo para logística."
    )
    assert page.file_name_label.text() == "Daniel_CV.docx"
    assert page.file_details_label.text() == "DOCX — 2.0 KB"
    assert page.file_integrity_label.text() == "Íntegro"

    assert service.document_service.verified == [
        service.curriculum
    ]


def test_show_document_handles_curriculum_without_file(
    qapp,
) -> None:
    page, service = _page()

    service.curriculum.file_relative_path = ""
    service.curriculum.file_original_name = ""

    page._show_document(service.curriculum)

    assert (
        page.file_name_label.text()
        == "Nenhum arquivo anexado"
    )
    assert page.file_details_label.text() == ""
    assert page.file_integrity_label.text() == "Sem arquivo"
    assert page.select_file_button.isEnabled()
    assert not page.open_file_button.isEnabled()


def test_delete_curriculum_requires_selection(
    qapp,
    monkeypatch,
) -> None:
    page, service = _page()

    page.current_curriculum_id = None

    infos: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda _parent, _title, message: infos.append(
            str(message)
        ),
    )

    page._delete_curriculum()

    assert service.deleted == []
    assert infos == [
        "Selecione um currículo para excluir."
    ]


def test_delete_curriculum_can_be_cancelled(
    qapp,
    monkeypatch,
) -> None:
    page, service = _page()

    page.current_curriculum_id = 1

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.No,
    )

    page._delete_curriculum()

    assert service.deleted == []


def test_delete_curriculum_success(
    qapp,
    monkeypatch,
) -> None:
    page, service = _page()

    page.current_curriculum_id = 1

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.Yes,
    )

    page._delete_curriculum()

    assert service.deleted == [
        (
            1,
            False,
        )
    ]
    assert page.current_curriculum_id is None


def test_delete_curriculum_false_result_warns(
    qapp,
    monkeypatch,
) -> None:
    page, service = _page()

    page.current_curriculum_id = 1
    service.delete_outcomes = [False]

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.Yes,
    )

    warnings: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: warnings.append(
            str(message)
        ),
    )

    page._delete_curriculum()

    assert warnings == [
        "O currículo não pôde ser excluído."
    ]


def test_delete_curriculum_integrity_error_can_cancel_cascade(
    qapp,
    monkeypatch,
) -> None:
    page, service = _page()

    page.current_curriculum_id = 1

    service.delete_outcomes = [
        IntegrityError("foreign key"),
    ]

    answers = iter(
        (
            QMessageBox.Yes,
            QMessageBox.No,
        )
    )

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: next(answers),
    )

    page._delete_curriculum()

    assert service.deleted == [
        (
            1,
            False,
        )
    ]


def test_delete_curriculum_integrity_error_can_cascade(
    qapp,
    monkeypatch,
) -> None:
    page, service = _page()

    page.current_curriculum_id = 1

    service.delete_outcomes = [
        IntegrityError("foreign key"),
        True,
    ]

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.Yes,
    )

    page._delete_curriculum()

    assert service.deleted == [
        (
            1,
            False,
        ),
        (
            1,
            True,
        ),
    ]

    assert page.current_curriculum_id is None


def test_delete_curriculum_non_integrity_error_is_reported(
    qapp,
    monkeypatch,
) -> None:
    page, service = _page()

    page.current_curriculum_id = 1

    service.delete_outcomes = [
        RuntimeError("database error"),
    ]

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.Yes,
    )

    messages: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda _parent, _title, message: messages.append(
            str(message)
        ),
    )

    page._delete_curriculum()

    assert messages == [
        "Não foi possível concluir a exclusão."
    ]


def test_open_curriculum_selects_existing_record(
    qapp,
) -> None:
    page, _service = _page()

    assert page.open_curriculum(1) is True

    assert page.current_curriculum_id == 1
    assert page.name_input.text() == "Currículo Principal"


def test_open_curriculum_returns_false_when_not_found(
    qapp,
) -> None:
    page, _service = _page()

    assert page.open_curriculum(999) is False


def test_refresh_reference_data_reloads_curricula(
    qapp,
    monkeypatch,
) -> None:
    page, _service = _page()

    calls: list[bool] = []

    monkeypatch.setattr(
        page,
        "_load_curricula",
        lambda: calls.append(True),
    )

    page.refresh_reference_data()

    assert calls == [True]


def test_search_curricula_uses_query_and_empty_query(
    qapp,
) -> None:
    page, service = _page()

    page.search_input.setText("logística")
    page._search_curricula()

    assert service.search_queries == [
        "logística"
    ]

    service.search_queries.clear()

    page.search_input.clear()
    page._search_curricula()

    assert service.search_queries == []


def test_clear_form_resets_fields(qapp) -> None:
    page, _service = _page()

    _fill_form(page)

    page.current_curriculum_id = 1
    page.pending_file_path = Path("curriculo.pdf")

    page._clear_form()

    assert page.current_curriculum_id is None
    assert page.pending_file_path is None
    assert page.name_input.text() == ""
    assert page.version_input.text() == ""
    assert page.language_input.text() == ""
    assert page.description_input.toPlainText() == ""
    assert (
        page.file_name_label.text()
        == "Nenhum arquivo anexado"
    )


def test_format_size_supports_bytes_kilobytes_and_megabytes() -> None:
    assert CurriculumPage._format_size(500) == "500 B"
    assert CurriculumPage._format_size(2048) == "2.0 KB"
    assert (
        CurriculumPage._format_size(2 * 1024 * 1024)
        == "2.0 MB"
    )


def test_integrity_error_helper_checks_exception_chain() -> None:
    assert _is_integrity_error(
        IntegrityError("fk")
    )

    outer = RuntimeError("outer")

    try:
        raise IntegrityError("inner")
    except IntegrityError as exc:
        outer.__cause__ = exc

    assert _is_integrity_error(outer)

    assert not _is_integrity_error(
        RuntimeError("generic")
    )
