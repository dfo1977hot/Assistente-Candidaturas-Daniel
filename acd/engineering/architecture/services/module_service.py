"""
Module service.

Builds ModuleInfo instances from ArchitectureVisitor objects.
"""

from __future__ import annotations

from pathlib import Path

from acd.engineering.architecture.models.module_info import (
    ModuleInfo,
)
from acd.engineering.architecture.models.source_location import (
    SourceLocation,
)
from acd.engineering.architecture.parser.architecture_visitor import (
    ArchitectureVisitor,
)


class ModuleService:
    """
    Creates ModuleInfo objects from parsed architecture data.
    """

    def build(
        self,
        *,
        module_name: str,
        package: str,
        source_file: Path,
        visitor: ArchitectureVisitor,
    ) -> ModuleInfo:
        """
        Builds a ModuleInfo instance.
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