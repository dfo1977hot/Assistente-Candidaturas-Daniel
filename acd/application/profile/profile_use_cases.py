from __future__ import annotations

from acd.services.profile_service import ProfileService, ProfileAggregate, ProfileCompletionService
from acd.services.import_service import ImportService
from acd.services.export_service import ExportService


class ProfileApplicationService:
    """Facade de aplicação para o módulo de profile engine."""

    def __init__(self) -> None:
        self.profile_service = ProfileService()
        self.completion_service = ProfileCompletionService()
        self.import_service = ImportService(self.profile_service)
        self.export_service = ExportService()

    def create_profile(self, *, full_name: str, email: str):
        return self.profile_service.create_profile(full_name=full_name, email=email)

    def update_profile(self, profile_id: int, **fields):
        return self.profile_service.update_profile(profile_id, **fields)

    def calculate_completion(self, aggregate: ProfileAggregate):
        return self.completion_service.calculate(aggregate)

    def import_profile(self, payload: dict[str, object], *, source: str):
        return self.import_service.import_data(payload, source=source)

    def export_profile(self, payload: dict[str, object], *, format: str):
        return self.export_service.export_data(payload, format=format)
