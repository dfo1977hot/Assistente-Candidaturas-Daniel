from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    MetaData,
    Table,
    create_engine,
    insert,
    select,
)
from sqlalchemy.orm import Session

from acd.infrastructure.database.dependency_delete import (
    ExtraDependency,
    delete_with_dependencies,
)


def test_delete_with_dependencies_removes_recursive_children() -> None:
    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()
    parents = Table("parents", metadata, Column("id", Integer, primary_key=True))
    children = Table(
        "children",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("parent_id", ForeignKey("parents.id"), nullable=False),
    )
    grandchildren = Table(
        "grandchildren",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("child_id", ForeignKey("children.id"), nullable=False),
    )
    metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(insert(parents).values(id=1))
        connection.execute(insert(children).values(id=10, parent_id=1))
        connection.execute(insert(grandchildren).values(id=100, child_id=10))
    with Session(engine) as session:
        assert delete_with_dependencies(session, table_name="parents", primary_key="id", value=1)
    with engine.connect() as connection:
        assert connection.execute(select(parents)).all() == []
        assert connection.execute(select(children)).all() == []
        assert connection.execute(select(grandchildren)).all() == []


def test_delete_with_extra_dependency_handles_legacy_column_without_fk() -> None:
    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()
    curricula = Table("curricula", metadata, Column("id", Integer, primary_key=True))
    applications = Table("applications", metadata, Column("id", Integer, primary_key=True), Column("curriculum_id", Integer))
    metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(insert(curricula).values(id=1))
        connection.execute(insert(applications).values(id=2, curriculum_id=1))
    with Session(engine) as session:
        assert delete_with_dependencies(session, table_name="curricula", primary_key="id", value=1, extra_dependencies=(ExtraDependency("applications", "curriculum_id"),))
    with engine.connect() as connection:
        assert connection.execute(select(curricula)).all() == []
        assert connection.execute(select(applications)).all() == []
