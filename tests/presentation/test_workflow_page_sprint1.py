from pathlib import Path


def test_workflow_page_contains_sprint1_designer_controls() -> None:
    source = Path("acd/presentation/pages/workflow_page.py").read_text(
        encoding="utf-8"
    )
    for text in (
        "Pesquisar workflows",
        "Usar template",
        "+ Adicionar",
        "Executar agora",
        "Cancelar",
        "Histórico",
        "Reexecutar etapa que falhou",
    ):
        assert text in source


def test_workflow_page_has_progress_and_keeps_current_record() -> None:
    source = Path("acd/presentation/pages/workflow_page.py").read_text(
        encoding="utf-8"
    )
    assert "QProgressBar" in source
    assert "self._select_workflow_row(workflow.id)" in source
    assert '"O registro foi salvo"' in source
