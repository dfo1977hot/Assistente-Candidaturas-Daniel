from pathlib import Path
import zipfile

import pytest

from acd.services.curriculum_document_service import (
    CurriculumDocumentError,
    CurriculumDocumentService,
)


class FakeCurriculum:
    def __init__(self) -> None:
        self.id = 1
        self.file_original_name = None
        self.file_relative_path = None
        self.file_extension = None
        self.file_mime_type = None
        self.file_size_bytes = None
        self.file_sha256 = None
        self.file_attached_at = None


class FakeRepository:
    def __init__(self) -> None:
        self.curriculum = FakeCurriculum()

    def get_by_id(self, curriculum_id: int):
        return self.curriculum if curriculum_id == 1 else None

    def update(self, curriculum):
        self.curriculum = curriculum
        return curriculum


def test_pdf_round_trip(tmp_path: Path) -> None:
    repo = FakeRepository()
    service = CurriculumDocumentService(repo, project_root=tmp_path)
    source = tmp_path / "cv.pdf"
    source.write_bytes(b"%PDF-1.7\nconteudo")
    saved = service.attach_document(1, source)
    stored = service.resolve_path(saved.file_relative_path)
    assert stored is not None and stored.exists()
    assert service.verify_integrity(saved).status == "verified"
    service.remove_document(1)
    assert not stored.exists()


def test_docx_is_accepted(tmp_path: Path) -> None:
    repo = FakeRepository()
    service = CurriculumDocumentService(repo, project_root=tmp_path)
    source = tmp_path / "cv.docx"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types />")
        archive.writestr("word/document.xml", "<document />")
    saved = service.attach_document(1, source)
    assert saved.file_extension == ".docx"


def test_invalid_extension_is_rejected(tmp_path: Path) -> None:
    repo = FakeRepository()
    service = CurriculumDocumentService(repo, project_root=tmp_path)
    source = tmp_path / "cv.txt"
    source.write_text("x", encoding="utf-8")
    with pytest.raises(CurriculumDocumentError, match="Formato não permitido"):
        service.attach_document(1, source)

class FailingRepository(FakeRepository):
    def update(self, curriculum):
        raise RuntimeError("falha simulada")


def test_replace_preserves_previous_file_when_database_update_fails(
    tmp_path: Path,
) -> None:
    repo = FakeRepository()
    service = CurriculumDocumentService(repo, project_root=tmp_path)
    first = tmp_path / "primeiro.pdf"
    first.write_bytes(b"%PDF-1.7\nprimeiro")
    saved = service.attach_document(1, first)
    previous_path = service.resolve_path(saved.file_relative_path)
    assert previous_path is not None and previous_path.exists()

    failing_repo = FailingRepository()
    failing_repo.curriculum = saved
    failing_service = CurriculumDocumentService(failing_repo, project_root=tmp_path)
    replacement = tmp_path / "substituto.pdf"
    replacement.write_bytes(b"%PDF-1.7\nsubstituto")

    with pytest.raises(RuntimeError, match="falha simulada"):
        failing_service.attach_document(1, replacement)

    assert previous_path.exists()
    managed_files = list(failing_service.storage_root.glob("*"))
    assert managed_files == [previous_path]
