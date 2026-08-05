"""Bounded validation for external documents without executing content."""

from __future__ import annotations

from dataclasses import dataclass
import io
import json
from pathlib import Path, PurePosixPath
import zipfile

from acd.security.secure_paths import validate_filename
from acd.security.security_errors import ExternalFileRejectedError, PathRejectedError

DEFAULT_MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_ZIP_MEMBERS = 1000
MAX_ZIP_EXPANDED_BYTES = 50 * 1024 * 1024
MAX_COMPRESSION_RATIO = 100
_ALLOWED = frozenset({".docx", ".pdf", ".csv", ".json", ".xml", ".png", ".jpg", ".jpeg"})


@dataclass(frozen=True, slots=True)
class ValidatedExternalFile:
    filename: str
    extension: str
    content: bytes


class ExternalFilePolicy:
    def __init__(self, *, max_bytes: int = DEFAULT_MAX_FILE_BYTES) -> None:
        if max_bytes <= 0:
            raise ValueError("Maximum file size must be positive")
        self.max_bytes = max_bytes

    def validate(self, filename: str, content: bytes) -> ValidatedExternalFile:
        try:
            safe_name = validate_filename(filename, allowed_extensions=_ALLOWED)
        except PathRejectedError as error:
            raise ExternalFileRejectedError(str(error)) from error
        if not content or len(content) > self.max_bytes:
            raise ExternalFileRejectedError("External file size is not allowed")
        extension = Path(safe_name).suffix.lower()
        validator = getattr(self, f"_validate_{extension[1:]}")
        validator(content)
        return ValidatedExternalFile(safe_name, extension, bytes(content))

    @staticmethod
    def _validate_docx(content: bytes) -> None:
        if not content.startswith(b"PK"):
            raise ExternalFileRejectedError("DOCX signature is invalid")
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                names = ExternalFilePolicy._validate_zip_members(archive)
                if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                    raise ExternalFileRejectedError("DOCX structure is invalid")
        except (zipfile.BadZipFile, RuntimeError) as error:
            raise ExternalFileRejectedError("DOCX container is invalid") from error

    @staticmethod
    def _validate_zip_members(archive: zipfile.ZipFile) -> frozenset[str]:
        members = archive.infolist()
        if len(members) > MAX_ZIP_MEMBERS:
            raise ExternalFileRejectedError("Archive contains too many members")
        expanded = 0
        names: set[str] = set()
        for member in members:
            path = PurePosixPath(member.filename)
            if path.is_absolute() or ".." in path.parts or "\\" in member.filename:
                raise ExternalFileRejectedError("Archive member path is unsafe")
            expanded += member.file_size
            if expanded > MAX_ZIP_EXPANDED_BYTES:
                raise ExternalFileRejectedError("Archive expanded size is excessive")
            if member.file_size and member.compress_size == 0:
                raise ExternalFileRejectedError("Archive compression ratio is invalid")
            if member.compress_size and member.file_size / member.compress_size > MAX_COMPRESSION_RATIO:
                raise ExternalFileRejectedError("Archive compression ratio is excessive")
            names.add(member.filename)
        return frozenset(names)

    @staticmethod
    def _validate_pdf(content: bytes) -> None:
        if not content.startswith(b"%PDF-"):
            raise ExternalFileRejectedError("PDF signature is invalid")

    @staticmethod
    def _validate_csv(content: bytes) -> None:
        ExternalFilePolicy._strict_utf8(content)

    @staticmethod
    def _validate_json(content: bytes) -> None:
        try:
            parsed = json.loads(ExternalFilePolicy._strict_utf8(content))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ExternalFileRejectedError("JSON content is invalid") from error
        if not isinstance(parsed, (dict, list)):
            raise ExternalFileRejectedError("JSON root type is not allowed")

    @staticmethod
    def _validate_xml(content: bytes) -> None:
        text = ExternalFilePolicy._strict_utf8(content)
        lowered = text.lower()
        if "<!doctype" in lowered or "<!entity" in lowered:
            raise ExternalFileRejectedError("XML entities and DTD are not allowed")
        try:
            from xml.etree import ElementTree

            ElementTree.fromstring(text)
        except ElementTree.ParseError as error:
            raise ExternalFileRejectedError("XML content is invalid") from error

    @staticmethod
    def _validate_png(content: bytes) -> None:
        if not content.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ExternalFileRejectedError("PNG signature is invalid")

    @staticmethod
    def _validate_jpg(content: bytes) -> None:
        if not content.startswith(b"\xff\xd8\xff"):
            raise ExternalFileRejectedError("JPEG signature is invalid")

    _validate_jpeg = _validate_jpg

    @staticmethod
    def _strict_utf8(content: bytes) -> str:
        try:
            return content.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise ExternalFileRejectedError("File encoding is invalid") from error

