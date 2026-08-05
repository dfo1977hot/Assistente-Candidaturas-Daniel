from acd.desktop_composition_root import DesktopCompositionRoot


def test_dashboard_renders_kpi_widgets(qapp):
    window = DesktopCompositionRoot().build_main_window()
    dashboard = window.dashboard

    for card in [
        dashboard.total_companies_card,
        dashboard.total_jobs_card,
        dashboard.total_applications_card,
        dashboard.total_interviews_card,
        dashboard.today_interviews_card,
        dashboard.total_curricula_card,
        dashboard.most_used_curriculum_card,
    ]:
        assert card.valor_label.text() is not None
