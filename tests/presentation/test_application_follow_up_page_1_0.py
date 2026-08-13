from pathlib import Path

SOURCE = Path("acd/presentation/pages/application_page.py").read_text(encoding="utf-8")


def test_application_save_preserves_current_record() -> None:
    assert "self._select_application_row(saved_application_id)" in SOURCE
    start = SOURCE.index("def _save_application")
    end = SOURCE.index("def _require_follow_up")
    save_block = SOURCE[start:end]
    assert "self._clear_form()" not in save_block


def test_timeline_has_filter_counter_and_structured_table() -> None:
    block = SOURCE[SOURCE.index("def _show_timeline"):SOURCE.index("def _load_follow_up_state")]
    assert 'type_filter.addItem("Todos")' in block
    assert 'counter.setText(f"{len(filtered)} evento(s)")' in block
    assert 'QTableWidget(0, 6)' in block
    assert '"Referência"' in block
