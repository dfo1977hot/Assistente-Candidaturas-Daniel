from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy import MetaData, Table, delete, inspect, select
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class ExtraDependency:
    child_table: str
    child_column: str


def delete_with_dependencies(
    session: Session,
    *,
    table_name: str,
    primary_key: str,
    value: int,
    extra_dependencies: Iterable[ExtraDependency] = (),
) -> bool:
    """Exclui um registro e seus dependentes dentro da mesma transação."""
    bind = session.get_bind()
    metadata = MetaData()
    inspector = inspect(bind)
    table_names = set(inspector.get_table_names())
    if table_name not in table_names:
        return False

    table_cache: dict[str, Table] = {}

    def table_for(name: str) -> Table:
        if name not in table_cache:
            table_cache[name] = Table(name, metadata, autoload_with=bind)
        return table_cache[name]

    root = table_for(table_name)
    exists = session.execute(
        select(root.c[primary_key]).where(root.c[primary_key] == value)
    ).first()
    if exists is None:
        return False

    visited: set[tuple[str, str, object]] = set()

    def remove_row(current_table_name: str, pk_name: str, pk_value: object) -> None:
        marker = (current_table_name, pk_name, pk_value)
        if marker in visited:
            return
        visited.add(marker)

        for child_name in table_names:
            child = table_for(child_name)
            primary_keys = list(child.primary_key.columns)
            for foreign_key in inspector.get_foreign_keys(child_name):
                if foreign_key.get("referred_table") != current_table_name:
                    continue
                constrained = foreign_key.get("constrained_columns") or []
                referred = foreign_key.get("referred_columns") or []
                if len(constrained) != 1 or len(referred) != 1 or referred[0] != pk_name:
                    continue
                child_fk = child.c[constrained[0]]
                if primary_keys:
                    child_pk = primary_keys[0]
                    child_values = session.execute(
                        select(child_pk).where(child_fk == pk_value)
                    ).scalars().all()
                    for child_value in child_values:
                        remove_row(child_name, child_pk.name, child_value)
                else:
                    session.execute(delete(child).where(child_fk == pk_value))

        if current_table_name == table_name:
            for dependency in extra_dependencies:
                if dependency.child_table not in table_names:
                    continue
                child = table_for(dependency.child_table)
                if dependency.child_column not in child.c:
                    continue
                primary_keys = list(child.primary_key.columns)
                condition = child.c[dependency.child_column] == pk_value
                if primary_keys:
                    child_pk = primary_keys[0]
                    child_values = session.execute(
                        select(child_pk).where(condition)
                    ).scalars().all()
                    for child_value in child_values:
                        remove_row(dependency.child_table, child_pk.name, child_value)
                else:
                    session.execute(delete(child).where(condition))

        current = table_for(current_table_name)
        session.execute(delete(current).where(current.c[pk_name] == pk_value))

    remove_row(table_name, primary_key, value)
    session.commit()
    return True
