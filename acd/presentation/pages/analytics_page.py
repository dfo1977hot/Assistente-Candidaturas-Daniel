from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from acd.presentation.pages.base_page import BasePage
from acd.services.analytics_service import AnalyticsService


class KPICard(QFrame):
    """Widget displaying a single KPI."""

    def __init__(self, title: str, value: str, subtitle: str = "") -> None:
        super().__init__()
        self.setStyleSheet(
            "QFrame { border: 1px solid #ddd; border-radius: 8px; background-color: #f9f9f9; padding: 12px; }"
        )

        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 10))
        title_label.setStyleSheet("color: #666;")

        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 24, QFont.Bold))
        value_label.setStyleSheet("color: #333;")

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setFont(QFont("Arial", 9))
            subtitle_label.setStyleSheet("color: #999;")
            layout.addWidget(subtitle_label)

        self.setLayout(layout)


class FunnelStage(QFrame):
    """Widget displaying a single stage in the conversion funnel."""

    def __init__(self, stage: str, count: int) -> None:
        super().__init__()
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)

        stage_label = QLabel(stage)
        stage_label.setFont(QFont("Arial", 11, QFont.Bold))

        count_label = QLabel(str(count))
        count_label.setFont(QFont("Arial", 14, QFont.Bold))
        count_label.setStyleSheet("color: #0066cc;")

        layout.addWidget(stage_label)
        layout.addWidget(count_label)

        self.setLayout(layout)
        self.setStyleSheet(
            "QFrame { border: 1px solid #ccc; border-radius: 4px; background-color: #fff; }"
        )


class RecommendationItem(QFrame):
    """Widget displaying a single recommendation."""

    def __init__(self, title: str, description: str, priority: str = "medium") -> None:
        super().__init__()
        layout = QVBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(12, 12, 12, 12)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 11, QFont.Bold))

        desc_label = QLabel(description)
        desc_label.setFont(QFont("Arial", 10))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666;")

        priority_label = QLabel(f"Prioridade: {priority.upper()}")
        priority_label.setFont(QFont("Arial", 9))

        priority_color = (
            "#dc3545" if priority == "high" else "#ffc107" if priority == "medium" else "#28a745"
        )
        priority_label.setStyleSheet(f"color: {priority_color};")

        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addWidget(priority_label)

        self.setLayout(layout)

        bg_color = (
            "#ffe6e6" if priority == "high" else "#fff9e6" if priority == "medium" else "#e6f9e6"
        )
        self.setStyleSheet(
            f"QFrame {{ border: 1px solid #ddd; border-radius: 4px; background-color: {bg_color}; }}"
        )


class AnalyticsPage(BasePage):
    """Analytics dashboard page showing metrics, KPIs, and recommendations."""

    def __init__(self, analytics_service: AnalyticsService) -> None:
        super().__init__("Analytics Dashboard")
        self.analytics_service = analytics_service
        self.setup_ui()

    def setup_ui(self) -> None:
        """Setup the analytics dashboard UI."""
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("Dashboard de Análise")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title)

        # Scroll area for all content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(20)
        scroll_layout.setContentsMargins(0, 0, 0, 0)

        # KPIs Section
        scroll_layout.addWidget(self.create_kpis_section())

        # Conversion Funnel Section
        scroll_layout.addWidget(self.create_funnel_section())

        # Trends Section
        scroll_layout.addWidget(self.create_trends_section())

        # Recommendations Section
        scroll_layout.addWidget(self.create_recommendations_section())

        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        self.setLayout(layout)

    def create_kpis_section(self) -> QWidget:
        """Create KPI cards section."""
        widget = QWidget()
        layout = QGridLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        # Fetch KPIs
        kpis = self.analytics_service.calculate_kpis()

        # Create KPI cards
        cards = [
            (
                "Conversão → Entrevista",
                kpis.get("conversion_to_interview", "0%"),
                "Taxa de sucesso",
            ),
            ("ATS Médio", kpis.get("average_ats", "0"), "Score de similaridade"),
            ("Melhor Plataforma", kpis.get("best_platform", "N/A"), "Maior taxa de sucesso"),
            ("Candidaturas", str(kpis.get("total_applications", 0)), "Total enviadas"),
            ("Entrevistas", str(kpis.get("interviews_scheduled", 0)), "Agendadas"),
            ("Ofertas", str(kpis.get("offers_received", 0)), "Recebidas"),
        ]

        for idx, (title, value, subtitle) in enumerate(cards):
            card = KPICard(title, value, subtitle)
            row = idx // 3
            col = idx % 3
            layout.addWidget(card, row, col)

        widget.setLayout(layout)
        return widget

    def create_funnel_section(self) -> QWidget:
        """Create conversion funnel section."""
        container = QFrame()
        container.setStyleSheet(
            "QFrame { border: 1px solid #ddd; border-radius: 8px; background-color: #f9f9f9; padding: 16px; }"
        )

        layout = QVBoxLayout()
        layout.setSpacing(12)

        title = QLabel("Funil de Conversão")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        # Fetch funnel data
        funnel = self.analytics_service.get_conversion_funnel()

        # Create funnel stages
        funnel_layout = QHBoxLayout()
        funnel_layout.setSpacing(8)

        for stage_data in funnel:
            stage = FunnelStage(stage_data["stage"], stage_data["count"])
            funnel_layout.addWidget(stage, 1)

        layout.addLayout(funnel_layout)
        container.setLayout(layout)
        return container

    def create_trends_section(self) -> QWidget:
        """Create trends analysis section."""
        container = QFrame()
        container.setStyleSheet(
            "QFrame { border: 1px solid #ddd; border-radius: 8px; background-color: #f9f9f9; padding: 16px; }"
        )

        layout = QVBoxLayout()
        layout.setSpacing(12)

        title = QLabel("Tendências")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        # Fetch trends
        dashboard = self.analytics_service.generate_dashboard()
        trends = dashboard.get("trends", {})

        trends_grid = QGridLayout()
        trends_grid.setSpacing(12)
        trends_grid.setContentsMargins(0, 0, 0, 0)

        # ATS Trend
        ats_trend = trends.get("ats", {})
        ats_label = QLabel(f"ATS: {ats_trend.get('trend', 'estável').upper()}")
        ats_label.setFont(QFont("Arial", 11))
        ats_color = (
            "#28a745"
            if ats_trend.get("trend") == "up"
            else "#dc3545" if ats_trend.get("trend") == "down" else "#666"
        )
        ats_label.setStyleSheet(f"color: {ats_color}; font-weight: bold;")
        trends_grid.addWidget(ats_label, 0, 0)

        # Conversion Trend
        conv_trend = trends.get("conversion", {})
        conv_label = QLabel(f"Conversão: {conv_trend.get('trend', 'estável').upper()}")
        conv_label.setFont(QFont("Arial", 11))
        conv_color = (
            "#28a745"
            if conv_trend.get("trend") == "up"
            else "#dc3545" if conv_trend.get("trend") == "down" else "#666"
        )
        conv_label.setStyleSheet(f"color: {conv_color}; font-weight: bold;")
        trends_grid.addWidget(conv_label, 0, 1)

        layout.addLayout(trends_grid)
        container.setLayout(layout)
        return container

    def create_recommendations_section(self) -> QWidget:
        """Create recommendations section."""
        container = QFrame()
        container.setStyleSheet(
            "QFrame { border: 1px solid #ddd; border-radius: 8px; background-color: #f9f9f9; padding: 16px; }"
        )

        layout = QVBoxLayout()
        layout.setSpacing(12)

        title = QLabel("Recomendações Estratégicas")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        # Fetch recommendations
        recommendations = self.analytics_service.get_recommendations()

        if recommendations:
            for rec in recommendations:
                item = RecommendationItem(
                    rec["title"], rec["description"], rec.get("priority", "medium")
                )
                layout.addWidget(item)
        else:
            no_rec_label = QLabel("Nenhuma recomendação no momento.")
            no_rec_label.setStyleSheet("color: #999;")
            layout.addWidget(no_rec_label)

        container.setLayout(layout)
        return container
