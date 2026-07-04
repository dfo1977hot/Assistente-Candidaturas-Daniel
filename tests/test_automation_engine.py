import os
import tempfile

import pytest

from acd.domain.entities.application import Application
from acd.domain.entities.curriculum import Curriculum
from acd.domain.entities.job import Job
from acd.domain.entities.job_profile import JobProfile
from acd.services.automation_service import AutomationService, AutomationContext
from acd.infrastructure.automation.connectors import MockConnector
from acd.infrastructure.automation.browser_manager import BrowserManager
from acd.infrastructure.automation.connector_factory import ConnectorFactory


@pytest.fixture
def automation_setup(monkeypatch):
    temp_dir = tempfile.mkdtemp(prefix="acd-automation-", dir=".")
    db_path = os.path.join(temp_dir, "test_acd_automation.db")
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

    import acd.domain.entities.application
    import acd.domain.entities.curriculum
    import acd.domain.entities.curriculum_version
    import acd.domain.entities.job
    import acd.domain.entities.job_profile
    import acd.domain.entities.automation_session
    import acd.domain.entities.automation_log
    import acd.domain.entities.automation_result
    import acd.domain.entities.connector_setting
    import acd.domain.entities.browser_profile

    Base.metadata.drop_all(bind=database_module.engine)
    Base.metadata.create_all(bind=database_module.engine)

    yield

    Base.metadata.drop_all(bind=database_module.engine)


def test_connector_factory_selects_mock_connector():
    factory = ConnectorFactory()
    connector = factory.create("smartrecruiters")
    assert connector is not None


def test_browser_manager_initializes_context():
    manager = BrowserManager()
    context = manager.create_context(headless=True)
    assert context["headless"] is True


def test_automation_service_executes_mock_flow(automation_setup):
    service = AutomationService()
    application = Application(job_id=1, company_id=1, status="Pronta para Aplicação")
    curriculum = Curriculum(name="Analista", description="Power BI, Excel")
    job = Job(title="Analista", company_id=1)
    job_profile = JobProfile(job_id=1, raw_description="Vaga de analista", skills="Power BI", technologies="Power BI", methodologies="", languages="", certifications="", keywords="Power BI")
    context = AutomationContext(application=application, curriculum=curriculum, job=job, job_profile=job_profile, platform="smartrecruiters", headless=True)

    result = service.run(context)

    assert result["status"] == "success"
    assert result["logs"]
