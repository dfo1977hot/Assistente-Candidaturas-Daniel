"""Canonical path authorization for untrusted relative names."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path, PurePath, PureWindowsPath
import re

from acd.security.security_errors import PathRejectedError

_WINDOWS_RESERVED = frozenset(
    {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
)
_SAFE_FILENAME = re.compile(r"^[^\x00-\x1f<>:\"/\\|?*]+$")


def validate_filename(
    name: str,
    *,
    allowed_extensions: frozenset[str] | None = None,
    reject_double_extension: bool = True,
) -> str:
    """Validate one portable leaf name and return its normalized form."""
    normalized = name.strip()
    windows = PureWindowsPath(normalized)
    if (
        not normalized
        or normalized in {".", ".."}
        or windows.is_absolute()
        or windows.drive
        or len(PurePath(normalized).parts) != 1
        or not _SAFE_FILENAME.fullmatch(normalized)
        or normalized.endswith((".", " "))
    ):
        raise PathRejectedError("Filename is not allowed")
    stem_head = normalized.split(".", 1)[0].upper()
    if stem_head in _WINDOWS_RESERVED:
        raise PathRejectedError("Filename is reserved")
    suffixes = [suffix.lower() for suffix in Path(normalized).suffixes]
    if allowed_extensions is not None:
        expected = frozenset(extension.lower() for extension in allowed_extensions)
        if not suffixes or suffixes[-1] not in expected:
            raise PathRejectedError("File extension is not allowed")
        if reject_double_extension and len(suffixes) > 1:
            raise PathRejectedError("Multiple file extensions are not allowed")
    return normalized


@dataclass(frozen=True, slots=True)
class AuthorizedPathPolicy:
    root: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", self.root.expanduser().resolve())

    def resolve_relative(
        self,
        value: str | Path,
        *,
        allowed_extensions: frozenset[str] | None = None,
    ) -> Path:
        raw = str(value)
        windows = PureWindowsPath(raw)
        if not raw.strip() or windows.is_absolute() or windows.drive or raw.startswith(("\\\\", "//")):
            raise PathRejectedError("Absolute or UNC path is not allowed")
        if any(part in {"", ".", ".."} for part in windows.parts):
            raise PathRejectedError("Path traversal is not allowed")
        parts = list(windows.parts)
        parts[-1] = validate_filename(parts[-1], allowed_extensions=allowed_extensions)
        candidate = self.root.joinpath(*parts).resolve(strict=False)
        try:
            if os.path.commonpath((str(self.root), str(candidate))) != str(self.root):
                raise PathRejectedError("Path is outside the authorized root")
        except ValueError as error:
            raise PathRejectedError("Path uses a different drive") from error
        return candidate

