import os
import tempfile

import pytest

from acd.infrastructure.repositories.skill_repository import SkillRepository
from acd.services.knowledge_service import KnowledgeService


@pytest.fixture
def knowledge_setup(monkeypatch):
    temp_dir = tempfile.mkdtemp(prefix="acd-knowledge-", dir=".")
    db_path = os.path.join(temp_dir, "test_acd.db")
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

    yield KnowledgeService(repository=SkillRepository())

    Base.metadata.drop_all(bind=database_module.engine)


def test_knowledge_service_creates_merges_and_searches(knowledge_setup):
    service = knowledge_setup

    created = service.create_skill(
        name="Power BI",
        category="TI",
        description="Ferramenta de visualização de dados",
        weight=0.8,
    )
    assert created.id is not None
    assert service.search_skills("power")[0].name == "Power BI"

    merged = service.merge_skill(
        source_skill_id=created.id,
        target_skill_id=created.id,
        alias_name="Microsoft Power BI",
    )
    assert merged is not None
    assert service.get_aliases(created.id)


def test_knowledge_service_creates_relations_and_similarity(knowledge_setup):
    service = knowledge_setup

    lean = service.create_skill(name="Lean", category="Produção", weight=0.7)
    kaizen = service.create_skill(name="Kaizen", category="Produção", weight=0.8)
    service.create_skill(name="Six Sigma", category="Qualidade", weight=0.9)

    relation = service.create_relation(
        parent_skill_id=lean.id,
        child_skill_id=kaizen.id,
        relation_type="Relacionado",
        strength=0.85,
    )
    assert relation is not None
    assert service.get_skill_tree()[0]["name"] == "Lean"

    similarity = service.calculate_similarity("Lean", "Kaizen")
    assert similarity >= 0.4

    stats = service.get_statistics()
    assert stats["skills"] >= 3
    assert stats["relations"] >= 1
    assert stats["categories"] >= 2

    assert service.classify_skill("Power BI") == "TI"
