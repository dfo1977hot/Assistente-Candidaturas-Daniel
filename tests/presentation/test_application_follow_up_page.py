from __future__ import annotations

from types import SimpleNamespace

from acd.presentation.pages.application_page import ApplicationPage


class FollowUpStub:
    ACTION_TYPES = ("Enviar follow-up", "Verificar status")
    INTERACTION_TYPES = ("Retorno recebido", "Outro")
    PRIORITIES = ("Normal", "Alta")

    def get_state(self, application_id):
        assert application_id == 7
        return SimpleNamespace(
            next_action="Enviar follow-up",
            priority="Alta",
            note="Acompanhar",
            follow_up_time="09:30",
            last_interaction_at=None,
            last_interaction_type="",
        )


def test_follow_up_controls_are_injected_and_response_date_is_read_only(qtbot):
    page = ApplicationPage(application_follow_up_service=FollowUpStub())
    qtbot.addWidget(page)
    page._load_follow_up_state(7)

    assert page.next_action_combo.currentText() == "Enviar follow-up"
    assert page.follow_up_priority_combo.currentText() == "Alta"
    assert page.follow_up_time_input.text() == "09:30"
    assert page.response_date_input.isReadOnly()
