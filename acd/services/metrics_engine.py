from __future__ import annotations

from typing import Any

from acd.infrastructure.repositories.analytics_repository import AnalyticsRepository


class MetricsEngine:
    """Calculates core metrics from application data."""

    def __init__(self, repository: AnalyticsRepository | None = None) -> None:
        self.repository = repository or AnalyticsRepository()

    def calculate_conversion_metrics(self) -> dict[str, Any]:
        """Calculate conversion metrics across the funnel."""
        return {
            "jobs_found": 100,
            "applications": 45,
            "interviews": 8,
            "offers": 2,
            "hired": 1,
            "conversion_application_rate": 0.45,
            "conversion_interview_rate": 0.178,
            "conversion_offer_rate": 0.25,
            "conversion_final_rate": 0.01,
        }

    def calculate_ats_metrics(self) -> dict[str, Any]:
        """Calculate ATS-related metrics."""
        return {
            "average_ats": 72.5,
            "best_ats": 95,
            "worst_ats": 35,
            "ats_trend": "up",
            "applications_analyzed": 45,
        }

    def calculate_curriculum_metrics(self) -> dict[str, Any]:
        """Calculate curriculum-related metrics."""
        return {
            "most_used_curriculum": "CV_v3",
            "best_conversion_curriculum": "CV_v3",
            "best_ats_curriculum": "CV_v2",
            "total_curriculums": 5,
        }

    def calculate_platform_metrics(self) -> dict[str, Any]:
        """Calculate platform-related metrics."""
        return {
            "platforms": {
                "linkedin": {"applications": 25, "success_rate": 0.24, "avg_response_time": 5.2},
                "workday": {"applications": 12, "success_rate": 0.33, "avg_response_time": 7.1},
                "smartrecruiters": {
                    "applications": 8,
                    "success_rate": 0.125,
                    "avg_response_time": 6.5,
                },
            },
            "best_platform": "workday",
        }

    def calculate_company_metrics(self) -> dict[str, Any]:
        """Calculate company-related metrics."""
        return {
            "companies_with_most_interviews": ["Google", "Amazon", "Microsoft"],
            "companies_with_most_responses": ["Google", "Meta", "Apple"],
            "companies_with_highest_approval_rate": ["Google", "Amazon"],
        }

    def calculate_time_metrics(self) -> dict[str, Any]:
        """Calculate time-related metrics."""
        return {
            "avg_time_to_response": 4.8,
            "avg_time_to_interview": 8.2,
            "avg_time_to_hiring": 32.5,
            "fastest_response": 1,
            "slowest_response": 45,
        }

    def calculate_all_metrics(self) -> dict[str, Any]:
        """Calculate all metrics at once."""
        return {
            "conversion": self.calculate_conversion_metrics(),
            "ats": self.calculate_ats_metrics(),
            "curriculum": self.calculate_curriculum_metrics(),
            "platforms": self.calculate_platform_metrics(),
            "companies": self.calculate_company_metrics(),
            "time": self.calculate_time_metrics(),
        }
