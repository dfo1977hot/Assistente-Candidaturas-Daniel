from acd.ui.dashboard import Dashboard


def test_dashboard_renders_kpi_widgets(qapp):
    dashboard = Dashboard()

    assert dashboard.total_companies_card is not None
    assert dashboard.total_jobs_card is not None
    assert dashboard.total_applications_card is not None
    assert dashboard.total_interviews_card is not None
    assert dashboard.today_interviews_card is not None
    assert dashboard.total_curricula_card is not None
    assert dashboard.most_used_curriculum_card is not None

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
