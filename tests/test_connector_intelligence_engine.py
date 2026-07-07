import os
import tempfile

import pytest

from acd.infrastructure.connectors.plugin_registry import PluginRegistry
from acd.infrastructure.repositories.connector_repository import ConnectorRepository
from acd.services.connector_discovery_service import ConnectorDiscoveryService
from acd.services.connector_mapping_service import MappingService
from acd.services.connector_transformation_service import TransformationService
from acd.services.connector_validation_service import ValidationService
from acd.services.field_resolver_service import FieldResolverService
from acd.services.schema_service import SchemaService


@pytest.fixture
def connector_setup(monkeypatch):
    temp_dir = tempfile.mkdtemp(prefix="acd-connectors-", dir=".")
    db_path = os.path.join(temp_dir, "test_acd_connectors.db")
    monkeypatch.setattr(
        "acd.database.database.DATABASE_URL",
        f"sqlite:///{db_path}",
    )

    import acd.database.database as database_module

    database_module.engine.dispose()
    database_module.engine = database_module.create_engine(
        f"sqlite:///{db_path}",
        echo=False,
        future=True,
    )
    database_module.SessionLocal = database_module.sessionmaker(
        bind=database_module.engine,
        autoflush=False,
        autocommit=False,
    )

    from acd.models.base import Base

    Base.metadata.drop_all(bind=database_module.engine)
    Base.metadata.create_all(bind=database_module.engine)

    yield

    Base.metadata.drop_all(bind=database_module.engine)


def test_mapping_service_builds_mapping(connector_setup):
    service = MappingService(repository=ConnectorRepository())
    mapping = service.create_mapping(
        platform_name="LinkedIn",
        source_field="Profile.full_name",
        target_field="First Name",
        transformation="trim",
        priority=10,
    )
    assert mapping is not None
    assert mapping.target_field == "First Name"


def test_validation_service_validates_payload(connector_setup):
    service = ValidationService()
    payload = {"email": "daniel@example.com", "phone": "+55 11 99999-9999", "required": "ok"}
    result = service.validate(payload)
    assert result["valid"] is True


def test_transformation_service_normalizes_values(connector_setup):
    service = TransformationService()
    result = service.apply("phone", "+55 11 99999-9999")
    assert result == "+55 11 99999-9999"


def test_discovery_service_detects_platform(connector_setup):
    service = ConnectorDiscoveryService()
    detected = service.detect("LinkedIn Easy Apply")
    assert detected == "linkedin"


def test_connector_repository_persists_platform_schema(connector_setup):
    repository = ConnectorRepository()
    platform = repository.create_platform("LinkedIn")
    assert platform.name == "LinkedIn"


def test_schema_service_registers_and_versions_schema(connector_setup):
    service = SchemaService(repository=ConnectorRepository())
    schema = service.register_schema("LinkedIn", "linkedin", version="2")
    assert schema.version == "2"


def test_field_resolver_matches_profile_fields(connector_setup):
    resolver = FieldResolverService()
    match = resolver.resolve("full_name", ["First Name", "Email", "Phone"])
    assert match == "First Name"


def test_plugin_registry_registers_connector_plugin(connector_setup):
    registry = PluginRegistry()
    registry.register("linkedin", lambda: {"name": "linkedin"})
    assert registry.get("linkedin")() == {"name": "linkedin"}
