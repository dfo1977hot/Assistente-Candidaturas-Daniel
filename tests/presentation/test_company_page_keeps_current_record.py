from pathlib import Path


def test_company_lookup_keeps_current_row_selected() -> None:
    source = Path("acd/presentation/pages/company_page.py").read_text(
        encoding="utf-8"
    )
    assert "self._apply_lookup_result(result)" in source
    assert "self._select_company_row_by_id(self.current_company_id)" in source


def test_company_save_keeps_current_record_selected() -> None:
    source = Path("acd/presentation/pages/company_page.py").read_text(
        encoding="utf-8"
    )
    assert "saved_company = self.service.create_company(" in source
    assert "saved_company = self.service.update_company(" in source
    assert "selected_company_id = self.current_company_id" in source
    assert "self._select_company_row_by_id(selected_company_id)" in source
    assert "def _select_company_row_by_id" in source
