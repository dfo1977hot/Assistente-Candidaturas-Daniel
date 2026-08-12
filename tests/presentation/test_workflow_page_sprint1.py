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


def test_workflow_page_collects_only_execution_context_ids() -> None:
    source = Path("acd/presentation/pages/workflow_page.py").read_text(
        encoding="utf-8"
    )
    assert 'context_row.addRow("Vaga alvo", self.job_combo)' in source
    assert 'context_row.addRow("Candidatura alvo", self.application_combo)' in source
    assert 'context_row.addRow("Currículo alvo", self.curriculum_combo)' in source
    assert 'context=self._execution_context()' in source
    assert '("job_id", self.job_combo)' in source
    assert '("application_id", self.application_combo)' in source
    assert '("curriculum_id", self.curriculum_combo)' in source
