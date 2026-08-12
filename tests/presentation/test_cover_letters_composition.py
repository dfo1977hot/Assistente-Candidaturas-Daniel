from pathlib import Path


def test_cover_letters_route_uses_letter_page() -> None:
    source = Path("acd/desktop_composition_root.py").read_text(encoding="utf-8")
    assert "from acd.presentation.pages.letter_page import LetterPage" in source
    assert '"cover_letters": LetterPage(' in source
    assert "cover_letter_service" in source
