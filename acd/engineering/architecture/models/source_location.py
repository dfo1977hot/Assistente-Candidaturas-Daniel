"""
Source code location model.

Represents the location of an element inside a Python source file.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class SourceLocation:
    """
    Represents the location of an element in a source file.

    Examples
    --------
    file.py
        line 10
        column 4

    file.py
        lines 10-25
    """

    file: Path
    start_line: int
    end_line: int
    start_column: int = 0
    end_column: int = 0

    @property
    def line_count(self) -> int:
        """
        Number of source lines occupied by the element.
        """

        return self.end_line - self.start_line + 1

    @property
    def is_single_line(self) -> bool:
        """
        True if the element occupies only one line.
        """

        return self.start_line == self.end_line

    @property
    def exists(self) -> bool:
        """
        Returns True if the source file exists.
        """

        return self.file.exists()

    def __str__(self) -> str:
        if self.is_single_line:
            return f"{self.file}:{self.start_line}"

        return (
            f"{self.file}:"
            f"{self.start_line}-{self.end_line}"
        )

    def __repr__(self) -> str:
        return (
            "SourceLocation("
            f"file={self.file!r}, "
            f"start_line={self.start_line}, "
            f"end_line={self.end_line})"
        )