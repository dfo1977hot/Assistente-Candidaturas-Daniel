"""
Module mapper.

Maps an ArchitectureVisitor into a ModuleInfo instance.
"""

from __future__ import annotations

from pathlib import Path

from acd.engineering.architecture.models.module_info import ModuleInfo
from acd.engineering.architecture.models.source_location import SourceLocation
from acd.engineering.architecture.parser.architecture_visitor import (
    ArchitectureVisitor,
)


class ModuleMapper:
    """
    Converts ArchitectureVisitor objects into ModuleInfo instances.
    """

    def map(
        self,
        *,
        module_name: str,
        package: str,
        source_file: Path,
        visitor: ArchitectureVisitor,
    ) -> ModuleInfo:
        """
        Maps a visitor into a ModuleInfo.
        """

        return ModuleInfo(
            name=module_name,
            package=package,
            location=SourceLocation(
                file=source_file,
                start_line=1,
                end_line=1,
            ),
            imports=visitor.imports.copy(),
            functions=visitor.functions.copy(),
            classes=visitor.classes.copy(),
        )