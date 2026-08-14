from __future__ import annotations

from PySide6.QtWidgets import QLabel

from acd.presentation.pages.analytics_page import (
    AnalyticsPage,
    FunnelStage,
    KPICard,
    RecommendationItem,
)


class _AnalyticsService:
    def __init__(self) -> None:
        self.kpis = {
            "conversion_to_interview": "35%",
            "average_ats": "82",
            "best_platform": "LinkedIn",
            "total_applications": 20,
            "interviews_scheduled": 7,
            "offers_received": 2,
        }

        self.funnel = [
            {
                "stage": "Candidaturas",
                "count": 20,
            },
            {
                "stage": "Entrevistas",
                "count": 7,
            },
            {
                "stage": "Ofertas",
                "count": 2,
            },
        ]

        self.dashboard = {
            "trends": {
                "ats": {
                    "trend": "up",
                },
                "conversion": {
                    "trend": "down",
                },
            }
        }

        self.recommendations = [
            {
                "title": "Melhorar ATS",
                "description": "Ajustar palavras-chave do currículo.",
                "priority": "high",
            },
            {
                "title": "Expandir canais",
                "description": "Testar novas plataformas.",
                "priority": "medium",
            },
            {
                "title": "Manter estratégia",
                "description": "Continuar acompanhando os indicadores.",
                "priority": "low",
            },
        ]

    def calculate_kpis(self):
        return dict(self.kpis)

    def get_conversion_funnel(self):
        return list(self.funnel)

    def generate_dashboard(self):
        return dict(self.dashboard)

    def get_recommendations(self):
        return list(self.recommendations)


def _texts(widget) -> list[str]:
    return [
        label.text()
        for label in widget.findChildren(QLabel)
    ]


def test_kpi_card_renders_title_value_and_subtitle(
    qapp,
) -> None:
    card = KPICard(
        "Conversão",
        "35%",
        "Taxa de sucesso",
    )

    texts = _texts(card)

    assert "Conversão" in texts
    assert "35%" in texts
    assert "Taxa de sucesso" in texts


def test_kpi_card_without_subtitle_renders_only_title_and_value(
    qapp,
) -> None:
    card = KPICard(
        "Candidaturas",
        "20",
    )

    texts = _texts(card)

    assert texts == [
        "Candidaturas",
        "20",
    ]


def test_funnel_stage_renders_stage_and_count(
    qapp,
) -> None:
    stage = FunnelStage(
        "Entrevistas",
        7,
    )

    texts = _texts(stage)

    assert "Entrevistas" in texts
    assert "7" in texts


def test_recommendation_item_supports_all_priorities(
    qapp,
) -> None:
    high = RecommendationItem(
        "Alta",
        "Descrição alta",
        "high",
    )
    medium = RecommendationItem(
        "Média",
        "Descrição média",
        "medium",
    )
    low = RecommendationItem(
        "Baixa",
        "Descrição baixa",
        "low",
    )

    assert "Prioridade: HIGH" in _texts(high)
    assert "Prioridade: MEDIUM" in _texts(medium)
    assert "Prioridade: LOW" in _texts(low)


def test_analytics_page_builds_all_sections(
    qapp,
) -> None:
    service = _AnalyticsService()

    page = AnalyticsPage(
        service,  # type: ignore[arg-type]
    )

    texts = _texts(page)

    assert "Dashboard de Análise" in texts

    assert "Conversão → Entrevista" in texts
    assert "35%" in texts

    assert "ATS Médio" in texts
    assert "82" in texts

    assert "Melhor Plataforma" in texts
    assert "LinkedIn" in texts

    assert "Candidaturas" in texts
    assert "20" in texts

    assert "Entrevistas" in texts
    assert "7" in texts

    assert "Ofertas" in texts
    assert "2" in texts

    assert "Funil de Conversão" in texts
    assert "Tendências" in texts
    assert "Recomendações Estratégicas" in texts

    assert "ATS: UP" in texts
    assert "Conversão: DOWN" in texts

    assert "Melhorar ATS" in texts
    assert "Expandir canais" in texts
    assert "Manter estratégia" in texts


def test_kpis_section_uses_defaults_for_missing_values(
    qapp,
) -> None:
    service = _AnalyticsService()
    service.kpis = {}

    page = AnalyticsPage(
        service,  # type: ignore[arg-type]
    )

    texts = _texts(page)

    assert "0%" in texts
    assert "0" in texts
    assert "N/A" in texts


def test_trends_section_supports_stable_defaults(
    qapp,
) -> None:
    service = _AnalyticsService()
    service.dashboard = {
        "trends": {}
    }

    page = AnalyticsPage(
        service,  # type: ignore[arg-type]
    )

    texts = _texts(page)

    assert "ATS: ESTÁVEL" in texts
    assert "Conversão: ESTÁVEL" in texts


def test_trends_section_supports_opposite_directions(
    qapp,
) -> None:
    service = _AnalyticsService()
    service.dashboard = {
        "trends": {
            "ats": {
                "trend": "down",
            },
            "conversion": {
                "trend": "up",
            },
        }
    }

    page = AnalyticsPage(
        service,  # type: ignore[arg-type]
    )

    texts = _texts(page)

    assert "ATS: DOWN" in texts
    assert "Conversão: UP" in texts


def test_recommendations_section_handles_empty_list(
    qapp,
) -> None:
    service = _AnalyticsService()
    service.recommendations = []

    page = AnalyticsPage(
        service,  # type: ignore[arg-type]
    )

    texts = _texts(page)

    assert "Nenhuma recomendação no momento." in texts


def test_recommendation_without_priority_uses_medium(
    qapp,
) -> None:
    service = _AnalyticsService()

    service.recommendations = [
        {
            "title": "Recomendação",
            "description": "Descrição",
        }
    ]

    page = AnalyticsPage(
        service,  # type: ignore[arg-type]
    )

    texts = _texts(page)

    assert "Recomendação" in texts
    assert "Prioridade: MEDIUM" in texts