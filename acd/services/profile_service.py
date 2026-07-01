from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from acd.domain.entities.profile import Profile
from acd.infrastructure.repositories.profile_repository import ProfileRepository


@dataclass
class ProfileAggregate:
    profile: dict[str, Any]
    experiences: list[dict[str, Any]] = field(default_factory=list)
    educations: list[dict[str, Any]] = field(default_factory=list)
    languages: list[dict[str, Any]] = field(default_factory=list)
    certifications: list[dict[str, Any]] = field(default_factory=list)
    projects: list[dict[str, Any]] = field(default_factory=list)
    publications: list[dict[str, Any]] = field(default_factory=list)
    social_links: list[dict[str, Any]] = field(default_factory=list)
    answer_templates: list[dict[str, Any]] = field(default_factory=list)


class ProfileService:
    """Cria e atualiza um perfil profissional central."""

    def __init__(self, repository: ProfileRepository | None = None) -> None:
        self.repository = repository or ProfileRepository()

    def create_profile(self, *, full_name: str, email: str) -> Profile:
        profile = Profile(full_name=full_name, email=email)
        return self.repository.create(profile)

    def update_profile(self, profile_id: int, **fields: Any) -> Profile | None:
        profile = self.repository.get_by_id(profile_id)
        if profile is None:
            return None
        for key, value in fields.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        return self.repository.update(profile)

    def get_profile(self, profile_id: int) -> Profile | None:
        return self.repository.get_by_id(profile_id)


class ProfileCompletionService:
    """Calcula percentual de conclusão do perfil."""

    def calculate(self, aggregate: ProfileAggregate) -> dict[str, Any]:
        completed_sections = []
        if aggregate.profile.get("full_name"):
            completed_sections.append("profile")
        if aggregate.experiences:
            completed_sections.append("experiences")
        if aggregate.educations:
            completed_sections.append("education")
        if aggregate.languages:
            completed_sections.append("languages")
        if aggregate.certifications:
            completed_sections.append("certifications")
        total_sections = 5
        percentage = round((len(completed_sections) / total_sections) * 100, 2)
        return {"percentage": percentage, "completed_sections": completed_sections}
