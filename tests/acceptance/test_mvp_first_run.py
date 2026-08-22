from __future__ import annotations


def test_mvp_first_run_opens_dashboard_and_routes(acceptance_runtime) -> None:
    window = acceptance_runtime.window

    assert acceptance_runtime.window.stack.count() == 15
    assert [window.sidebar.item(index).text() for index in range(window.sidebar.count())] == [
        "🏠 Dashboard",
        "🏢 Empresas",
        "💼 Vagas",
        "📄 Currículos",
        "✉️ Cartas",
        "🎯 Candidaturas",
        "🗣️ Entrevistas",
        "📊 CRM",
        "⚙️ Workflows",
        "📈 Análise",
        "🎯 Planejamento de Carreira",
        "🤖 Assistente IA",
        "🦾 Agentes",
        "\U0001F464 Perfil do Candidato",
        "⚙ Configurações",
    ]
    assert "applications/new" not in window.router.pages
    assert "new_application" not in window.router.pages

    window.router.navigate("dashboard")
    assert window.stack.currentWidget() is window.dashboard

    window.router.navigate("applications")
    assert window.stack.currentWidget() is window.application_page

    assert window.dashboard.total_companies_card.valor_label.text() == "0"
    assert window.dashboard.total_jobs_card.valor_label.text() == "0"
    assert window.dashboard.total_applications_card.valor_label.text() == "0"
    assert window.dashboard.total_interviews_card.valor_label.text() == "0"
    assert window.dashboard.total_curricula_card.valor_label.text() == "0"
    assert window.dashboard.most_used_curriculum_card.valor_label.text() == "0"

