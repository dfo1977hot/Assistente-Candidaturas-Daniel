from acd.ui.main_window import MainWindow


def test_main_window_initializes(qapp):
    window = MainWindow()

    assert window.windowTitle() == "Assistente de Candidaturas do Daniel"
    assert window.sidebar is not None
    assert window.stack is not None
    assert window.stack.count() >= 14
