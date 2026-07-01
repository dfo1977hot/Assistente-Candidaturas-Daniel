from __future__ import annotations

from typing import Optional

from sqlalchemy import select

from acd.database import database as database_module
from acd.domain.connector.platform import Platform
from acd.domain.connector.schema import PlatformSchema
from acd.domain.connector.field_mapping import FieldMapping


class ConnectorRepository:
    """Repositório para esquemas, mappings e plataformas."""

    def create_platform(self, name: str) -> Platform:
        with database_module.SessionLocal() as session:
            platform = Platform(name=name)
            session.add(platform)
            session.commit()
            session.refresh(platform)
            return platform

    def create_schema(self, *, platform_id: int, name: str, version: str = "1") -> PlatformSchema:
        with database_module.SessionLocal() as session:
            schema = PlatformSchema(platform_id=platform_id, name=name, version=version)
            session.add(schema)
            session.commit()
            session.refresh(schema)
            return schema

    def create_mapping(self, *, platform_id: int, source_field: str, target_field: str, transformation: str = "", priority: int = 0) -> FieldMapping:
        with database_module.SessionLocal() as session:
            mapping = FieldMapping(
                platform_id=platform_id,
                source_field=source_field,
                target_field=target_field,
                transformation=transformation,
                priority=priority,
            )
            session.add(mapping)
            session.commit()
            session.refresh(mapping)
            return mapping

    def get_platform(self, platform_id: int) -> Optional[Platform]:
        with database_module.SessionLocal() as session:
            return session.get(Platform, platform_id)

    def list_platforms(self) -> list[Platform]:
        with database_module.SessionLocal() as session:
            return list(session.scalars(select(Platform)).all())
