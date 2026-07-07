from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from acd.presentation.pages.base_page import BasePage
from acd.services.career_planning_service import CareerPlanningService
from acd.services.gap_analysis_service import GapAnalysisService


class GoalCard(QFrame):
    """Widget displaying a career goal."""

    def __init__(self, goal: dict) -> None:
        super().__init__()
        self.setStyleSheet(
            "QFrame { border: 1px solid #ddd; border-radius: 8px; background-color: #f9f9f9; padding: 12px; }"
        )

        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel(goal.get("target_role", ""))
        title.setFont(QFont("Arial", 12, QFont.Bold))

        industry = QLabel(f"Indústria: {goal.get('target_industry', '')}")
        industry.setFont(QFont("Arial", 10))
        industry.setStyleSheet("color: #666;")

        compatibility = QLabel(f"Compatibilidade: {goal.get('compatibility', 0):.1f}%")
        compatibility.setFont(QFont("Arial", 10, QFont.Bold))
        compatibility.setStyleSheet("color: #0066cc;")

        layout.addWidget(title)
        layout.addWidget(industry)
        layout.addWidget(compatibility)

        self.setLayout(layout)


class SkillGapItem(QFrame):
    """Widget displaying a skill gap."""

    def __init__(self, skill: dict) -> None:
        super().__init__()
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)

        skill_label = QLabel(
            f"{skill['skill']} (Nível {skill['current']:.1f} → {skill['required']:.1f})"
        )
        skill_label.setFont(QFont("Arial", 10, QFont.Bold))

        severity_colors = {
            "critical": "#dc3545",
            "high": "#fd7e14",
            "medium": "#ffc107",
            "low": "#28a745",
        }
        severity = skill.get("severity", "medium")
        severity_label = QLabel(f"Severidade: {severity.upper()}")
        severity_label.setFont(QFont("Arial", 9))
        severity_label.setStyleSheet(f"color: {severity_colors.get(severity, '#666')};")

        layout.addWidget(skill_label)
        layout.addWidget(severity_label)

        self.setLayout(layout)

        bg_colors = {
            "critical": "#ffe6e6",
            "high": "#fff3cd",
            "medium": "#fff9e6",
            "low": "#e6f9e6",
        }
        self.setStyleSheet(
            f"QFrame {{ border: 1px solid #ddd; border-radius: 4px; background-color: {bg_colors.get(severity, '#fff')}; }}"
        )


class MilestoneItem(QFrame):
    """Widget displaying a milestone."""

    def __init__(self, milestone: dict) -> None:
        super().__init__()
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)

        title = QLabel(milestone.get("title", ""))
        title.setFont(QFont("Arial", 10, QFont.Bold))

        date = QLabel(f"Data: {milestone.get('target_date', '')[:10]}")
        date.setFont(QFont("Arial", 9))
        date.setStyleSheet("color: #666;")

        layout.addWidget(title)
        layout.addWidget(date)

        self.setLayout(layout)
        self.setStyleSheet(
            "QFrame { border: 1px solid #ccc; border-radius: 4px; background-color: #fff; }"
        )


class CareerPage(BasePage):
    """Career planning and intelligence page."""

    def __init__(self) -> None:
        super().__init__("Planejamento de Carreira")
        self.career_service = CareerPlanningService()
        self.gap_service = GapAnalysisService()
        self.setup_ui()

    def setup_ui(self) -> None:
        """Setup the career planning UI."""
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("Planejamento de Carreira")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title)

        # Create goal section
        layout.addWidget(self.create_goal_section())

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(16)
        scroll_layout.setContentsMargins(0, 0, 0, 0)

        # Goals section
        scroll_layout.addWidget(self.create_goals_section())

        # Gap analysis section
        scroll_layout.addWidget(self.create_gaps_section())

        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        self.setLayout(layout)

    def create_goal_section(self) -> QWidget:
        """Create section for adding new goal."""
        widget = QFrame()
        widget.setStyleSheet(
            "QFrame { border: 1px solid #ddd; border-radius: 8px; background-color: #f9f9f9; padding: 16px; }"
        )

        layout = QGridLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        # Labels
        layout.addWidget(QLabel("Cargo:"), 0, 0)
        layout.addWidget(QLabel("Indústria:"), 0, 2)

        # Input fields
        role_input = QLineEdit()
        role_input.setPlaceholderText("Ex: Coordenador de Supply Chain")
        layout.addWidget(role_input, 0, 1)

        industry_input = QLineEdit()
        industry_input.setPlaceholderText("Ex: Logística")
        layout.addWidget(industry_input, 0, 3)

        # More fields
        layout.addWidget(QLabel("Prazo (meses):"), 1, 0)
        months_input = QSpinBox()
        months_input.setMinimum(1)
        months_input.setMaximum(60)
        months_input.setValue(12)
        layout.addWidget(months_input, 1, 1)

        layout.addWidget(QLabel("Prioridade:"), 1, 2)
        priority_input = QComboBox()
        priority_input.addItems(["Alta", "Média", "Baixa"])
        layout.addWidget(priority_input, 1, 3)

        # Create button
        create_btn = QPushButton("Criar Objetivo")
        create_btn.setStyleSheet(
            "QPushButton { background-color: #0066cc; color: white; padding: 8px; border-radius: 4px; }"
        )
        layout.addWidget(create_btn, 2, 0, 1, 4)

        widget.setLayout(layout)
        return widget

    def create_goals_section(self) -> QWidget:
        """Create section showing active goals."""
        container = QFrame()
        container.setStyleSheet(
            "QFrame { border: 1px solid #ddd; border-radius: 8px; background-color: #f9f9f9; padding: 16px; }"
        )

        layout = QVBoxLayout()
        layout.setSpacing(12)

        title = QLabel("Objetivos Ativos")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        # Get active goals
        goals = self.career_service.list_active_goals()

        if goals:
            for goal in goals[:5]:  # Show top 5
                card = GoalCard(goal)
                layout.addWidget(card)
        else:
            no_goals = QLabel("Nenhum objetivo definido")
            no_goals.setStyleSheet("color: #999;")
            layout.addWidget(no_goals)

        layout.addStretch()
        container.setLayout(layout)
        return container

    def create_gaps_section(self) -> QWidget:
        """Create section showing skill gaps."""
        container = QFrame()
        container.setStyleSheet(
            "QFrame { border: 1px solid #ddd; border-radius: 8px; background-color: #f9f9f9; padding: 16px; }"
        )

        layout = QVBoxLayout()
        layout.setSpacing(12)

        title = QLabel("Lacunas de Competência")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        # This would show gaps for first active goal
        goals = self.career_service.list_active_goals()

        if goals:
            gaps_list = self.gap_service.get_gap_details(goals[0]["id"])
            gaps = gaps_list.get("gaps", [])

            if gaps:
                for gap in gaps[:5]:  # Show top 5 gaps
                    item = SkillGapItem(gap)
                    layout.addWidget(item)
            else:
                no_gaps = QLabel("Nenhuma lacuna identificada")
                no_gaps.setStyleSheet("color: #999;")
                layout.addWidget(no_gaps)
        else:
            no_data = QLabel("Crie um objetivo para análise de lacunas")
            no_data.setStyleSheet("color: #999;")
            layout.addWidget(no_data)

        layout.addStretch()
        container.setLayout(layout)
        return container
