"""
Tests for the automatic SQLAlchemy model registry.

These tests ensure that every ORM model is imported correctly and
registered in Base.metadata before the application starts.

Responsibilities of this test module:

- model registration;
- mapper configuration;
- metadata consistency;
- expected tables;
- basic structural validation.

Deep metadata validation (Foreign Keys, Constraints, Indexes,
Relationships, etc.) belongs to test_metadata_integrity.py.
"""

from __future__ import annotations

from sqlalchemy.orm import configure_mappers

import acd.database.model_registry  # noqa: F401
from acd.models.base import Base

# ==========================================================
# Expected tables
# ==========================================================

EXPECTED_TABLES = {
    #
    # Multi-Agent
    #
    "agents",
    "agent_sessions",
    "agent_messages",
    "agent_memory",
    "agent_tools",
    "agent_capabilities",
    "multi_agent_tasks",
    #
    # Legacy Agent
    #
    "agent_goals",
    "execution_plans",
    "plan_tasks",
    "reasoning_steps",
    "tool_calls",
    #
    # Core entities
    #
    "applications",
    "curricula",
    "curriculum_versions",
    "jobs",
    "job_profiles",
}


# ==========================================================
# Metadata
# ==========================================================


def test_metadata_is_not_empty() -> None:
    """
    Base.metadata must contain registered tables.
    """

    assert Base.metadata.tables
    assert len(Base.metadata.tables) > 0


def test_every_table_has_columns() -> None:
    """
    Every ORM table must expose at least one column.
    """

    for table in Base.metadata.tables.values():
        assert len(table.columns) >= 1, (
            f"Table '{table.name}' has no columns."
        )


def test_every_table_has_primary_key() -> None:
    """
    Every ORM table must define a Primary Key.
    """

    for table in Base.metadata.tables.values():
        assert table.primary_key.columns, (
            f"Table '{table.name}' has no Primary Key."
        )


def test_primary_key_columns_are_named() -> None:
    """
    Every Primary Key column must have a valid name.
    """

    for table in Base.metadata.tables.values():
        for column in table.primary_key.columns:
            assert column.name, (
                f"Unnamed Primary Key column in '{table.name}'."
            )


def test_every_table_belongs_to_base_metadata() -> None:
    """
    Every table must belong to Base.metadata.
    """

    for table in Base.metadata.tables.values():
        assert table.metadata is Base.metadata


def test_registered_table_objects_are_unique() -> None:
    """
    Each registered table must be represented by a unique object.
    """

    object_ids = [
        id(table)
        for table in Base.metadata.tables.values()
    ]

    assert len(object_ids) == len(set(object_ids))


# ==========================================================
# Mapper configuration
# ==========================================================


def test_sqlalchemy_can_configure_every_mapper() -> None:
    """
    SQLAlchemy must configure every mapper successfully.
    """

    configure_mappers()


# ==========================================================
# Expected tables
# ==========================================================


def test_expected_tables_are_registered() -> None:
    """
    Core ORM tables must always be available.
    """

    registered = set(Base.metadata.tables.keys())

    missing = EXPECTED_TABLES - registered

    assert not missing, (
        "Missing ORM tables:\n"
        + "\n".join(sorted(missing))
    )


# ==========================================================
# Metadata ordering
# ==========================================================


def test_metadata_can_be_sorted() -> None:
    """
    SQLAlchemy must be able to compute the dependency graph.
    """

    ordered_tables = list(Base.metadata.sorted_tables)

    assert ordered_tables
    assert len(ordered_tables) == len(Base.metadata.tables)


# ==========================================================
# Naming conventions
# ==========================================================


def test_table_names_follow_convention() -> None:
    """
    Table names should follow snake_case conventions.
    """

    for table in Base.metadata.tables.values():

        assert table.name == table.name.lower()

        assert " " not in table.name

        assert "-" not in table.name


# ==========================================================
# Registry sanity
# ==========================================================


def test_model_registry_loaded_expected_amount_of_tables() -> None:
    """
    Sanity check.

    A sudden reduction in the number of mapped tables usually
    indicates that one or more ORM modules are no longer being
    imported by model_registry.py.
    """

    assert len(Base.metadata.tables) >= 15