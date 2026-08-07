from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import os
from pathlib import Path
import re
import shutil
from uuid import uuid4
import zipfile

from acd.core.logger import logger
from acd.domain.entities.curriculum import Curriculum
from acd.infrastructure.repositories.curriculum_repository import CurriculumRepository


class CurriculumDocumentError(ValueError):
    """Erro funcional ao manipular documentos de currículo."""


@dataclass(frozen=True)
class DocumentIntegrity:
    status: str
    message: str


class CurriculumDocumentService:
    ALLOWED_EXTENSIONS = frozenset({".docx", ".pdf"})
    MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024

    def __init__(
        self,
        repository: CurriculumRepository | None = None,
        project_root: Path | None = None,
    ) -> None:
        self.repository = repository or CurriculumRepository()
        self.project_root = (project_root or Path.cwd()).resolve()
        self.storage_root = (
            self.project_root / "data" / "documents" / "curricula"
        ).resolve()
        self.storage_root.mkdir(parents=True, exist_ok=True)

    def attach_document(self, curriculum_id: int, source_path: str | Path) -> Curriculum:
        curriculum = self._require_curriculum(curriculum_id)
        source = Path(source_path).expanduser().resolve()
        self._validate_source(source)
        destination = self._new_destination(source)
        shutil.copy2(source, destination)
        previous = self.resolve_path(curriculum.file_relative_path)
        try:
            self._apply_metadata(curriculum, source, destination)
            updated = self.repository.update(curriculum)
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        if previous and previous != destination:
            previous.unlink(missing_ok=True)
        logger.info("Documento anexado ao currículo %s", curriculum_id)
        return updated

    def remove_document(self, curriculum_id: int) -> Curriculum:
        curriculum = self._require_curriculum(curriculum_id)
        document = self.resolve_path(curriculum.file_relative_path)
        self._clear_metadata(curriculum)
        updated = self.repository.update(curriculum)
        if document:
            document.unlink(missing_ok=True)
        return updated

    def duplicate_document(self, source: Curriculum, target: Curriculum) -> Curriculum:
        source_path = self.resolve_path(source.file_relative_path)
        if source_path is None or not source_path.exists():
            return target
        return self.attach_document(target.id, source_path)

    def open_document(self, curriculum_id: int) -> None:
        curriculum = self._require_curriculum(curriculum_id)
        path = self.resolve_path(curriculum.file_relative_path)
        if path is None or not path.exists():
            raise CurriculumDocumentError("Arquivo não encontrado.")
        try:
            os.startfile(path)  # type: ignore[attr-defined]
        except OSError as exc:
            raise CurriculumDocumentError(
                "Não foi possível abrir o arquivo no aplicativo padrão do Windows."
            ) from exc

    def verify_integrity(self, curriculum: Curriculum) -> DocumentIntegrity:
        if not curriculum.file_relative_path:
            return DocumentIntegrity("none", "Sem arquivo")
        path = self.resolve_path(curriculum.file_relative_path)
        if path is None or not path.exists():
            return DocumentIntegrity("missing", "Arquivo não encontrado")
        try:
            checksum = self.calculate_sha256(path)
        except OSError:
            return DocumentIntegrity("error", "Erro de leitura")
        if curriculum.file_sha256 and checksum != curriculum.file_sha256:
            return DocumentIntegrity("changed", "Arquivo alterado externamente")
        return DocumentIntegrity("verified", "Verificada")

    def resolve_path(self, relative_path: str | None) -> Path | None:
        if not relative_path:
            return None
        candidate = (self.project_root / relative_path).resolve()
        self._assert_managed(candidate)
        return candidate

    @staticmethod
    def calculate_sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _require_curriculum(self, curriculum_id: int) -> Curriculum:
        curriculum = self.repository.get_by_id(curriculum_id)
        if curriculum is None:
            raise CurriculumDocumentError("Currículo não encontrado.")
        return curriculum

    def _validate_source(self, source: Path) -> None:
        if not source.is_file():
            raise CurriculumDocumentError("Selecione um arquivo existente.")
        extension = source.suffix.lower()
        if extension not in self.ALLOWED_EXTENSIONS:
            raise CurriculumDocumentError(
                "Formato não permitido. Selecione um arquivo DOCX ou PDF."
            )
        if source.stat().st_size > self.MAX_FILE_SIZE_BYTES:
            raise CurriculumDocumentError(
                "O arquivo excede o limite máximo permitido de 20 MB."
            )
        if extension == ".pdf":
            with source.open("rb") as stream:
                if stream.read(5) != b"%PDF-":
                    raise CurriculumDocumentError("O arquivo selecionado não é um PDF válido.")
        else:
            try:
                with zipfile.ZipFile(source) as archive:
                    names = set(archive.namelist())
                    valid = "[Content_Types].xml" in names and any(
                        name.startswith("word/") for name in names
                    )
                    if not valid:
                        raise CurriculumDocumentError(
                            "O arquivo selecionado não é um DOCX válido."
                        )
            except zipfile.BadZipFile as exc:
                raise CurriculumDocumentError(
                    "O arquivo selecionado não é um DOCX válido."
                ) from exc

    def _new_destination(self, source: Path) -> Path:
        stem = re.sub(r"[^a-zA-Z0-9_-]+", "-", source.stem).strip("-").lower()
        destination = self.storage_root / f"{uuid4()}-{stem[:80] or 'curriculo'}{source.suffix.lower()}"
        self._assert_managed(destination)
        return destination

    def _apply_metadata(self, curriculum: Curriculum, source: Path, destination: Path) -> None:
        extension = source.suffix.lower()
        curriculum.file_original_name = source.name
        curriculum.file_relative_path = destination.relative_to(self.project_root).as_posix()
        curriculum.file_extension = extension
        curriculum.file_mime_type = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }[extension]
        curriculum.file_size_bytes = destination.stat().st_size
        curriculum.file_sha256 = self.calculate_sha256(destination)
        curriculum.file_attached_at = datetime.now(UTC).replace(tzinfo=None)

    @staticmethod
    def _clear_metadata(curriculum: Curriculum) -> None:
        for attribute in (
            "file_original_name", "file_relative_path", "file_extension",
            "file_mime_type", "file_size_bytes", "file_sha256", "file_attached_at",
        ):
            setattr(curriculum, attribute, None)

    def _assert_managed(self, path: Path) -> None:
        try:
            path.resolve().relative_to(self.storage_root)
        except ValueError as exc:
            raise CurriculumDocumentError(
                "O caminho do documento está fora da pasta administrada."
            ) from exc
