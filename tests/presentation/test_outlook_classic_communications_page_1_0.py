from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_application_page_exposes_outlook_classic_sync_without_infrastructure_import() -> None:
    source = (ROOT / "acd" / "presentation" / "pages" / "application_page.py").read_text(
        encoding="utf-8"
    )
    assert "Sincronizar Outlook Classic" in source
    assert "_CommunicationsData" in source
    assert "ClassicOutlookMailReader" not in source
    assert "win32com" not in source
    assert "pythoncom" not in source


def test_desktop_root_composes_outlook_classic_adapter_behind_communications_service() -> None:
    source = (ROOT / "acd" / "desktop_composition_root.py").read_text(encoding="utf-8")
    assert "ClassicOutlookMailReader()" in source
    assert "CommunicationsService(" in source
    assert "communications_service=communications_service" in source


def test_outlook_sync_runs_through_long_running_executor() -> None:
    source = (ROOT / "acd" / "presentation" / "pages" / "application_page.py").read_text(
        encoding="utf-8"
    )
    assert "_communications_executor = LongRunningTaskExecutor(self)" in source
    assert "_communications_executor.execute_with_context" in source
