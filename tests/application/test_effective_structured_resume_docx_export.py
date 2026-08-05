"""Tests for read-only effective structured resume DOCX export."""

from __future__ import annotations

from pathlib import Path

from acd.application.application_resume_source import ApplicationResumeSource
from acd.application.effective_application_resume_use_case import (
    EffectiveApplicationResumeResult,
    EffectiveApplicationResumeStatus,
)
from acd.application.effective_structured_resume_docx_export import (
    EffectiveStructuredResumeDocxExportStatus,
    ExportEffectiveStructuredResumeDocxRequest,
    ExportEffectiveStructuredResumeDocxUseCase,
)
from acd.application.structured_resume_snapshot import (
    StructuredResumeContentStatus,
    StructuredResumeIdentity,
    StructuredResumeSnapshot,
)


class _EffectiveResumeUseCase:
    def __init__(self, result: EffectiveApplicationResumeResult) -> None:
        self.result = result
        self.requests: list[object] = []

    def execute(self, request: object) -> EffectiveApplicationResumeResult:
        self.requests.append(request)
        return self.result


class _Exporter:
    def __init__(self) -> None:
        self.calls: list[tuple[StructuredResumeSnapshot, Path]] = []

    def export(self, snapshot: StructuredResumeSnapshot, destination_path: Path) -> None:
        self.calls.append((snapshot, destination_path))


def test_exports_only_the_effective_original_snapshot(tmp_path) -> None:
    snapshot = StructuredResumeSnapshot(1, identity=StructuredResumeIdentity("Daniel"))
    resolver = _EffectiveResumeUseCase(
        EffectiveApplicationResumeResult(
            EffectiveApplicationResumeStatus.SUCCESS,
            42,
            curriculum_id=10,
            structured_resume=snapshot,
            structured_content_status=StructuredResumeContentStatus.AVAILABLE,
        )
    )
    exporter = _Exporter()
    use_case = ExportEffectiveStructuredResumeDocxUseCase(resolver, exporter)  # type: ignore[arg-type]
    destination = tmp_path / "Daniel resume.docx"

    result = use_case.execute(ExportEffectiveStructuredResumeDocxRequest(42, destination))

    assert result.status is EffectiveStructuredResumeDocxExportStatus.SUCCESS
    assert result.exported
    assert result.source is ApplicationResumeSource.ORIGINAL
    assert exporter.calls == [(snapshot, destination)]
    assert resolver.requests[0].application_id == 42


def test_rejects_missing_structured_content_without_exporting(tmp_path) -> None:
    resolver = _EffectiveResumeUseCase(
        EffectiveApplicationResumeResult(
            EffectiveApplicationResumeStatus.SUCCESS,
            42,
            curriculum_id=10,
            resume_source=ApplicationResumeSource.RESUME_VERSION,
        )
    )
    exporter = _Exporter()
    use_case = ExportEffectiveStructuredResumeDocxUseCase(resolver, exporter)  # type: ignore[arg-type]

    result = use_case.execute(
        ExportEffectiveStructuredResumeDocxRequest(42, tmp_path / "resume.docx")
    )

    assert result.status is EffectiveStructuredResumeDocxExportStatus.STRUCTURED_CONTENT_REQUIRED
    assert not result.exported
    assert exporter.calls == []
