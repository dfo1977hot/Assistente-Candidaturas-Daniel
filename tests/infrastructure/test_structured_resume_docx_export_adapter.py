"""Real DOCX tests for the structured resume export adapter."""

from __future__ import annotations

from docx import Document

from acd.application.structured_resume_snapshot import (
    StructuredResumeExperience,
    StructuredResumeIdentity,
    StructuredResumeSnapshot,
)
from acd.infrastructure.structured_resume_docx_export_adapter import (
    PythonDocxStructuredResumeExportAdapter,
)


def test_adapter_writes_reopenable_docx_with_structured_sections(tmp_path) -> None:
    snapshot = StructuredResumeSnapshot(
        1,
        identity=StructuredResumeIdentity("Dаниel", "Software Engineer", "São Paulo"),
        skills=("Python", "DDD"),
        experiences=(
            StructuredResumeExperience("ACD", "Engineer", achievements=("Entrega contínua",)),
        ),
    )
    destination = tmp_path / "currículos" / "Daniel currículo.docx"
    destination.parent.mkdir()

    PythonDocxStructuredResumeExportAdapter().export(snapshot, destination)

    reopened = Document(destination)
    text = "\n".join(paragraph.text for paragraph in reopened.paragraphs)
    assert destination.stat().st_size > 0
    assert "Dаниel" in text
    assert "COMPETÊNCIAS" in text
    assert "EXPERIÊNCIA PROFISSIONAL" in text
    assert "Entrega contínua" in text
