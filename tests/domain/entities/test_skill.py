"""Tests for Skill-related entities."""

from __future__ import annotations

from acd.domain.entities.skill import (
    Skill,
    SkillAlias,
    SkillCategory,
    SkillRelation,
    SkillWeight,
)


def test_skill_category_defaults() -> None:
    """SkillCategory should initialize without persisted defaults."""

    category = SkillCategory()

    assert category.name is None
    assert category.description is None
    assert category.parent_id is None


def test_skill_category_assign_attributes() -> None:
    """SkillCategory should store assigned attributes."""

    category = SkillCategory(
        name="Supply Chain",
        description="Competências relacionadas à cadeia de suprimentos.",
        parent_id=1,
    )

    assert category.name == "Supply Chain"
    assert (
        category.description
        == "Competências relacionadas à cadeia de suprimentos."
    )
    assert category.parent_id == 1


def test_skill_defaults() -> None:
    """Skill should initialize without persisted defaults."""

    skill = Skill()

    assert skill.name is None
    assert skill.category is None
    assert skill.description is None
    assert skill.weight is None
    assert skill.active is None


def test_skill_assign_attributes() -> None:
    """Skill should store assigned attributes."""

    skill = Skill(
        name="Power BI",
        category="Business Intelligence",
        description="Ferramenta para dashboards.",
        weight=9.5,
        active=True,
    )

    assert skill.name == "Power BI"
    assert skill.category == "Business Intelligence"
    assert skill.description == "Ferramenta para dashboards."
    assert skill.weight == 9.5
    assert skill.active is True


def test_skill_alias_assign_attributes() -> None:
    """SkillAlias should store assigned attributes."""

    alias = SkillAlias(
        skill_id=10,
        alias_name="Microsoft Power BI",
    )

    assert alias.skill_id == 10
    assert alias.alias_name == "Microsoft Power BI"


def test_skill_relation_assign_attributes() -> None:
    """SkillRelation should store assigned attributes."""

    relation = SkillRelation(
        parent_skill_id=1,
        child_skill_id=2,
        relation_type="Relacionado",
        strength=0.85,
    )

    assert relation.parent_skill_id == 1
    assert relation.child_skill_id == 2
    assert relation.relation_type == "Relacionado"
    assert relation.strength == 0.85


def test_skill_weight_assign_attributes() -> None:
    """SkillWeight should store assigned attributes."""

    weight = SkillWeight(
        skill_id=5,
        weight=7.5,
        source="manual",
    )

    assert weight.skill_id == 5
    assert weight.weight == 7.5
    assert weight.source == "manual"


def test_skill_relationship_collections() -> None:
    """Relationship collections should be initialized."""

    skill = Skill()

    assert skill.aliases is not None
    assert isinstance(skill.aliases, list)

    assert skill.weights is not None
    assert isinstance(skill.weights, list)


def test_skill_category_relationship_collections() -> None:
    """Relationship collections should be initialized."""

    category = SkillCategory()

    assert category.children is not None
    assert isinstance(category.children, list)