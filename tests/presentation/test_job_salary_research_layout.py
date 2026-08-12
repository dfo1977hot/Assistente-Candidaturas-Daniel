from pathlib import Path


def test_job_page_exposes_salary_research_action_at_page_end() -> None:
    source = Path("acd/presentation/pages/job_page.py").read_text(encoding="utf-8")

    assert 'QPushButton("Pesquisar média salarial com IA")' in source
    assert "self.salary_research_button.clicked.connect(self._research_salary)" in source
    assert "SalaryResearchRequest(" in source
    assert "work_model=self.work_model_combo.currentText().strip()" in source
    assert (
        "employment_type=self.employment_type_combo.currentText().strip()"
        in source
    )
    assert source.index("self.layout.addWidget(self.table)") < source.index(
        "self.layout.addLayout(actions)"
    )



def test_salary_research_success_updates_ideal_and_persists_job() -> None:
    source = Path("acd/presentation/pages/job_page.py").read_text(encoding="utf-8")
    method = source.split(
        "    def _on_salary_research_succeeded", 1
    )[1].split("    def _on_salary_research_failed", 1)[0]

    assert "self.salary_min_input.setValue(result.salary_min)" not in method
    assert "self.salary_max_input.setValue(result.salary_max)" in method
    assert "self._save_job(clear_after=False, show_success=False)" in method
    assert "Pesquisa salarial concluída" not in method
    assert "Fontes consultadas" not in method
    assert "QMessageBox.information" not in method
    assert "QMessageBox.question" not in method
