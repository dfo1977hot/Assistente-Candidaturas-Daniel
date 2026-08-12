from pathlib import Path


def test_letter_page_contains_sprint_1_actions() -> None:
    source = Path("acd/presentation/pages/letter_page.py").read_text(
        encoding="utf-8"
    )
    for label in (
        "Gerar com IA",
        "Salvar",
        "Copiar",
        "Exportar DOCX",
        "Exportar PDF",
        "Currículo",
        "Vaga",
        "Assunto",
        "Carta",
    ):
        assert label in source


def test_letter_page_preserves_selected_record_after_save_and_generation() -> None:
    source = Path("acd/presentation/pages/letter_page.py").read_text(
        encoding="utf-8"
    )
    assert "self._select_row(saved.id)" in source
    assert "self._select_row(generated.id)" in source
