from __future__ import annotations

from typing import Any
import json


class ContextBuilder:
    """Builds comprehensive context for agent decisions."""

    def __init__(self) -> None:
        self._context: dict[str, Any] = {}

    def add_user_profile(self, profile: dict[str, Any]) -> ContextBuilder:
        """Add user profile information."""
        self._context["user_profile"] = {
            "skills": profile.get("skills", []),
            "certifications": profile.get("certifications", []),
            "experience_years": profile.get("experience_years", 0),
            "preferred_roles": profile.get("preferred_roles", []),
            "preferred_locations": profile.get("preferred_locations", []),
        }
        return self

    def add_career_goals(self, goals: list[dict[str, Any]]) -> ContextBuilder:
        """Add active career goals."""
        self._context["career_goals"] = goals
        return self

    def add_active_applications(self, applications: list[dict[str, Any]]) -> ContextBuilder:
        """Add active job applications."""
        self._context["active_applications"] = {
            "total": len(applications),
            "pending": len([a for a in applications if a.get("status") == "pending"]),
            "interviews": len([a for a in applications if a.get("status") == "interview"]),
            "rejected": len([a for a in applications if a.get("status") == "rejected"]),
        }
        return self

    def add_available_curricula(self, curricula: list[dict[str, Any]]) -> ContextBuilder:
        """Add available curriculum versions."""
        self._context["available_curricula"] = {
            "total": len(curricula),
            "versions": [{"id": c.get("id"), "specialization": c.get("specialization")} for c in curricula],
        }
        return self

    def add_job_preferences(self, preferences: dict[str, Any]) -> ContextBuilder:
        """Add job search preferences."""
        self._context["job_preferences"] = {
            "desired_salary_min": preferences.get("salary_min"),
            "desired_salary_max": preferences.get("salary_max"),
            "work_model": preferences.get("work_model", "hybrid"),
            "industries": preferences.get("industries", []),
            "company_sizes": preferences.get("company_sizes", []),
        }
        return self

    def add_analytics(self, analytics: dict[str, Any]) -> ContextBuilder:
        """Add analytics and performance metrics."""
        self._context["analytics"] = {
            "conversion_rate": analytics.get("conversion_rate", 0),
            "average_ats_score": analytics.get("average_ats_score", 0),
            "applications_per_week": analytics.get("applications_per_week", 0),
            "interview_rate": analytics.get("interview_rate", 0),
        }
        return self

    def add_recent_decisions(self, decisions: list[dict[str, Any]]) -> ContextBuilder:
        """Add recent agent decisions."""
        self._context["recent_decisions"] = decisions[-10:]  # Last 10 decisions
        return self

    def add_constraints(self, constraints: dict[str, Any]) -> ContextBuilder:
        """Add operational constraints."""
        self._context["constraints"] = {
            "max_daily_applications": constraints.get("max_daily_applications", 10),
            "min_match_score": constraints.get("min_match_score", 0.6),
            "require_human_approval": constraints.get("require_human_approval", False),
            "allowed_working_hours": constraints.get("allowed_working_hours", "09:00-18:00"),
        }
        return self

    def build(self) -> dict[str, Any]:
        """Build and return complete context."""
        return self._context.copy()

    def get_context_summary(self) -> str:
        """Get a summary of context for LLM prompts."""
        summary_parts = []

        if "user_profile" in self._context:
            profile = self._context["user_profile"]
            summary_parts.append(
                f"User Skills: {', '.join(profile.get('skills', []))} | "
                f"Experience: {profile.get('experience_years')} years"
            )

        if "career_goals" in self._context:
            goals = self._context["career_goals"]
            summary_parts.append(f"Active Goals: {len(goals)} | Primary: {goals[0].get('title') if goals else 'None'}")

        if "active_applications" in self._context:
            apps = self._context["active_applications"]
            summary_parts.append(
                f"Applications: {apps['total']} total | "
                f"{apps['pending']} pending | "
                f"{apps['interviews']} interviews"
            )

        if "analytics" in self._context:
            analytics = self._context["analytics"]
            summary_parts.append(
                f"Performance: {analytics.get('conversion_rate', 0):.1%} conversion | "
                f"{analytics.get('interview_rate', 0):.1%} interview rate"
            )

        return " | ".join(summary_parts)

    def to_json(self) -> str:
        """Convert context to JSON for storage or transmission."""
        return json.dumps(self._context, indent=2, ensure_ascii=False, default=str)

    def get_available_tools_context(self, tool_registry) -> str:
        """Get tools context for agent."""
        tools = tool_registry.get_all_tools()
        context = "Available Tools:\n"
        for tool in tools:
            context += f"\n- {tool.name}: {tool.description}\n"
            context += f"  Category: {tool.category}\n"
        return context
