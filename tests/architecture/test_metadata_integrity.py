"""
Deep integrity tests for the SQLAlchemy ORM metadata.

These tests validate the complete SQLAlchemy metadata graph after all
ORM models have been imported.

Responsibilities of this module:

- mapper integrity;
- Foreign Keys;
- metadata consistency;
- indexes;
- constraints;
- dependency graph.

Model registration itself is validated in
test_model_registry.py.
"""

from __future__ import annotations

from collections import Counter

import pytest
from sqlalchemy.exc import NoReferencedTableError
from sqlalchemy.orm import configure_mappers

import acd.database.model_registry  # noqa: F401
from acd.models.base import Base

# ==========================================================
# Mapper integrity
# ==========================================================


def test_all_mappers_can_be_configured() -> None:
    """
    Every SQLAlchemy mapper must configure successfully.
    """

    configure_mappers()


# ==========================================================
# Foreign Keys
# ==========================================================


def test_every_foreign_key_is_resolved() -> None:
    """
    Every ForeignKey must point to an existing table.
    """

    for table in Base.metadata.sorted_tables:

        for fk in table.foreign_keys:

            try:

                assert fk.column is not None

            except NoReferencedTableError as exc:

                pytest.fail(
                    "\n"
                    f"Broken ForeignKey\n\n"
                    f"Table      : {table.name}\n"
                    f"Column     : {fk.parent.name}\n"
                    f"References : {fk.target_fullname}\n\n"
                    f"{exc}"
                )


def test_every_foreign_key_parent_belongs_to_table() -> None:
    """
    Every ForeignKey parent column must belong to its table.
    """

    for table in Base.metadata.tables.values():

        for fk in table.foreign_keys:

            assert fk.parent.table is table


# ==========================================================
# Constraints
# ==========================================================


def test_constraint_names_are_unique() -> None:
    """
    Named constraints must be unique.
    """

    names: list[str] = []

    for table in Base.metadata.tables.values():

        for constraint in table.constraints:

            if constraint.name:

                names.append(constraint.name)

    duplicates = [

        name

        for name, amount in Counter(names).items()

        if amount > 1

    ]

    assert duplicates == []


# ==========================================================
# Indexes
# ==========================================================


def test_index_names_are_unique() -> None:
    """
    Named indexes must be unique.
    """

    names: list[str] = []

    for table in Base.metadata.tables.values():

        for index in table.indexes:

            if index.name:

                names.append(index.name)

    duplicates = [

        name

        for name, amount in Counter(names).items()

        if amount > 1

    ]

    assert duplicates == []


# ==========================================================
# Relationships
# ==========================================================


def test_relationship_targets_are_registered() -> None:
    """
    Every relationship target should be resolvable.

    configure_mappers() performs the heavy validation.
    This test guarantees every mapper has been inspected.
    """

    configure_mappers()

    for mapper in Base.registry.mappers:

        assert mapper.class_ is not None

        for relationship in mapper.relationships:

            assert relationship.mapper.class_ is not None


# ==========================================================
# Metadata consistency
# ==========================================================


def test_every_table_has_metadata_reference() -> None:
    """
    Every table must belong to Base.metadata.
    """

    for table in Base.metadata.tables.values():

        assert table.metadata is Base.metadata


def test_every_table_has_columns() -> None:
    """
    Metadata must not contain empty tables.
    """

    for table in Base.metadata.tables.values():

        assert len(table.columns) >= 1


def test_column_names_are_unique_inside_table() -> None:
    """
    Duplicate column names are not allowed.
    """

    for table in Base.metadata.tables.values():

        names = [

            column.name

            for column in table.columns

        ]

        assert len(names) == len(set(names))


# ==========================================================
# Dependency graph
# ==========================================================


def test_metadata_dependency_graph_is_valid() -> None:
    """
    SQLAlchemy must be able to compute the dependency graph.
    """

    ordered = list(Base.metadata.sorted_tables)

    assert ordered

    assert len(ordered) == len(Base.metadata.tables)


# ==========================================================
# Registry consistency
# ==========================================================


def test_metadata_registry_is_consistent() -> None:
    """
    Every registered table must belong to Base.metadata.
    """

    for name, table in Base.metadata.tables.items():

        assert table.name == name

        assert table.metadata is Base.metadata


# ==========================================================
# Smoke
# ==========================================================


def test_metadata_smoke() -> None:
    """
    Final ORM integrity smoke test.
    """

    configure_mappers()

    assert Base.metadata.tables

    assert list(Base.metadata.sorted_tables)