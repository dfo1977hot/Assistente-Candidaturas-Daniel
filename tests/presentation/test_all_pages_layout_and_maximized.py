from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _assert_order(source: str, *fragments: str) -> None:
    positions = [source.index(fragment) for fragment in fragments]
    assert positions == sorted(positions)


def test_company_page_places_search_and_table_before_form() -> None:
    source = _read("acd/presentation/pages/company_page.py")
    _assert_order(
        source,
        "self.layout.addLayout(search_layout)",
        "self.layout.addWidget(self.table)",
        "self.layout.addLayout(form_columns)",
        "self.layout.addLayout(full_width_fields)",
        "self.layout.addLayout(actions)",
    )


def test_curriculum_page_places_search_and_table_before_form() -> None:
    source = _read("acd/presentation/pages/curriculum_page.py")
    _assert_order(
        source,
        "self.layout.addLayout(search_layout)",
        "self.layout.addWidget(self.table)",
        "self.layout.addLayout(form_columns)",
        "self.layout.addLayout(full_width_fields)",
        "self.layout.addLayout(actions)",
    )


def test_interview_page_places_search_filters_and_table_before_form() -> None:
    source = _read("acd/presentation/pages/interview_page.py")
    _assert_order(
        source,
        "self.layout.addLayout(search_layout)",
        "self.layout.addLayout(filter_layout)",
        "self.layout.addWidget(self.table)",
        "self.layout.addLayout(form_columns)",
        "self.layout.addLayout(full_width_fields)",
        "self.layout.addLayout(actions)",
    )


def test_application_page_places_search_filters_and_table_before_form() -> None:
    source = _read("acd/presentation/pages/application_page.py")
    _assert_order(
        source,
        "self.content_layout.addLayout(search_layout)",
        "self.content_layout.addLayout(filter_layout)",
        "self.content_layout.addWidget(self.table)",
        "self.content_layout.addLayout(form_columns)",
        "self.content_layout.addLayout(full_width_fields)",
        "self.content_layout.addLayout(actions)",
    )


def test_main_window_respects_configured_startup_mode() -> None:
    source = _read("acd/ui/main_window.py")
    assert "from PySide6.QtCore import QTimer" in source
    assert 'self._settings_service.startup_mode() == "minimized"' in source
    assert "self.showMinimized" in source
    assert "self.showMaximized" in source
    assert "QTimer.singleShot(0, startup_method)" in source
