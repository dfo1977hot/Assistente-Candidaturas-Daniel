from acd.desktop_composition_root import DesktopCompositionRoot


def test_main_window_initializes_from_composed_dependencies(qapp):
    window = DesktopCompositionRoot().build_main_window()

    assert window.windowTitle() == "Assistente de Candidaturas do Daniel"
    assert window.sidebar is not None
    assert window.stack.count() == 14


def test_main_window_routes_candidate_decision_action(qapp, monkeypatch):
    window = DesktopCompositionRoot().build_main_window()
    destinations: list[str] = []
    monkeypatch.setattr(window.router, "navigate", destinations.append)

    window.navigate_candidate_decision_action("prepare_interview")

    assert destinations == ["interviews"]
