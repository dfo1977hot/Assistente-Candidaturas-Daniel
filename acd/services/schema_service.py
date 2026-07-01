from __future__ import annotations

from acd.domain.connector.schema import PlatformSchema
from acd.infrastructure.repositories.connector_repository import ConnectorRepository


class SchemaService:
    """Registra e versiona esquemas de plataformas."""

    def __init__(self, repository: ConnectorRepository | None = None) -> None:
        self.repository = repository or ConnectorRepository()

    def register_schema(self, platform_name: str, schema_name: str, *, version: str = "1") -> PlatformSchema:
        platform = self._get_or_create_platform(platform_name)
        return self.repository.create_schema(platform_id=platform.id, name=schema_name, version=version)

    def _get_or_create_platform(self, platform_name: str) -> object:
        platforms = self.repository.list_platforms()
        for platform in platforms:
            if platform.name.lower() == platform_name.lower():
                return platform
        return self.repository.create_platform(platform_name)
