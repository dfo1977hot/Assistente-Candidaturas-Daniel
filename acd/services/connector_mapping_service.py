from __future__ import annotations

from acd.domain.connector.field_mapping import FieldMapping
from acd.infrastructure.repositories.connector_repository import ConnectorRepository


class MappingService:
    """Cria e gerencia mapeamentos entre perfil e plataforma."""

    def __init__(self, repository: ConnectorRepository | None = None) -> None:
        self.repository = repository or ConnectorRepository()

    def create_mapping(self, *, platform_name: str, source_field: str, target_field: str, transformation: str = "", priority: int = 0) -> FieldMapping:
        platform = self._get_or_create_platform(platform_name)
        return self.repository.create_mapping(
            platform_id=platform.id,
            source_field=source_field,
            target_field=target_field,
            transformation=transformation,
            priority=priority,
        )

    def _get_or_create_platform(self, platform_name: str) -> object:
        platforms = self.repository.list_platforms()
        for platform in platforms:
            if platform.name.lower() == platform_name.lower():
                return platform
        return self.repository.create_platform(platform_name)
