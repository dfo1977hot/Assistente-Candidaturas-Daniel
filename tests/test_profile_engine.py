import os
import tempfile

import pytest

from acd.services.profile_service import ProfileService, ProfileAggregate, ProfileCompletionService
from acd.infrastructure.repositories.profile_repository import ProfileRepository
from acd.services.import_service import ImportService
from acd.services.export_service import ExportService


@pytest.fixture
def profile_setup(monkeypatch):
    temp_dir = tempfile.mkdtemp(prefix="acd-profile-", dir=".")
    db_path = os.path.join(temp_dir, "test_acd_profile.db")
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

    import acd.domain.entities.profile
    import acd.domain.entities.experience
    import acd.domain.entities.education
    import acd.domain.entities.language
    import acd.domain.entities.certification
    import acd.domain.entities.project
    import acd.domain.entities.publication
    import acd.domain.entities.social_link
    import acd.domain.entities.answer_template
    import acd.domain.entities.profile_version

    Base.metadata.drop_all(bind=database_module.engine)
    Base.metadata.create_all(bind=database_module.engine)

    yield

    Base.metadata.drop_all(bind=database_module.engine)


def test_profile_service_creates_and_updates_profile(profile_setup):
    service = ProfileService(repository=ProfileRepository())
    profile = service.create_profile(full_name="Daniel Silva", email="daniel@example.com")

    updated = service.update_profile(profile.id, summary="Engenheiro de software")
    assert updated is not None
    assert updated.summary == "Engenheiro de software"


def test_profile_completion_service_calculates_completion(profile_setup):
    service = ProfileCompletionService()
    aggregate = ProfileAggregate(profile={"full_name": "Daniel", "email": "d@example.com"}, experiences=[], educations=[], languages=[], certifications=[], projects=[], publications=[], social_links=[], answer_templates=[])
    result = service.calculate(aggregate)

    assert result["percentage"] >= 0
    assert result["completed_sections"]


def test_import_service_imports_linkedin_payload(profile_setup):
    service = ImportService()
    payload = {"full_name": "Daniel Silva", "email": "daniel@example.com", "experiences": [{"company": "ACME", "role": "Analista"}]}
    imported = service.import_data(payload, source="linkedin")
    assert imported["profile_id"] is not None


def test_export_service_exports_json(profile_setup):
    service = ExportService()
    payload = {"full_name": "Daniel Silva", "email": "daniel@example.com"}
    exported = service.export_data(payload, format="json")
    assert "full_name" in exported
