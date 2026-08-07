from acd.presentation.pages.application_wizard import (
    ApplicationWizard,
)


def test_create_wizard(qtbot):
    wizard = ApplicationWizard()

    qtbot.addWidget(wizard)

    assert wizard.stack.count() == 1