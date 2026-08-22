from __future__ import annotations

import pytest

from acd.services.curriculum_document_service import (
    CurriculumDocumentError,
    CurriculumDocumentService,
)


def test_reconcile_accepts_blocks_out_of_order() -> None:
    original = ("A", "B", "C")
    content = "[[BLOCO 3]] C3\n[[BLOCO 1]] A1\n[[BLOCO 2]] B2"

    result = CurriculumDocumentService._reconcile_optimized_blocks(
        content,
        original,
    )

    assert result == ("A1", "B2", "C3")


def test_reconcile_preserves_original_when_model_omits_indexed_block() -> None:
    original = ("A", "B", "C")
    content = "[[BLOCO 1]] A1\n[[BLOCO 3]] C3"

    result = CurriculumDocumentService._reconcile_optimized_blocks(
        content,
        original,
    )

    assert result == ("A1", "B", "C3")


def test_reconcile_accepts_harmless_markdown_around_marker() -> None:
    original = ("A", "B")
    content = "**[[BLOCO 2]]**: B2\n- [[BLOCO 1]] A1"

    result = CurriculumDocumentService._reconcile_optimized_blocks(
        content,
        original,
    )

    assert result == ("A1", "B2")


def test_reconcile_rejects_duplicate_block() -> None:
    with pytest.raises(CurriculumDocumentError, match="duplicado"):
        CurriculumDocumentService._reconcile_optimized_blocks(
            "[[BLOCO 1]] A1\n[[BLOCO 1]] A2",
            ("A",),
        )


def test_reconcile_rejects_out_of_range_block() -> None:
    with pytest.raises(CurriculumDocumentError, match="não existe"):
        CurriculumDocumentService._reconcile_optimized_blocks(
            "[[BLOCO 2]] B",
            ("A",),
        )


def test_reconcile_keeps_legacy_strict_block_count() -> None:
    with pytest.raises(CurriculumDocumentError, match="quantidade de blocos"):
        CurriculumDocumentService._reconcile_optimized_blocks(
            "A1\nB1",
            ("A", "B", "C"),
        )
