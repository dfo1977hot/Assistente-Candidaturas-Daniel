from __future__ import annotations

from acd.domain.knowledge.knowledge_node import KnowledgeNode, KnowledgeNodeType


def test_knowledge_node_represents_a_versioned_domain_projection() -> None:
    """A semantic node retains identity, type, attributes, and version."""
    node = KnowledgeNode(
        node_id="candidate:42",
        node_type=KnowledgeNodeType.CANDIDATE,
        attributes={"name": "Daniel"},
        version=2,
    )

    assert node.node_id == "candidate:42"
    assert node.node_type is KnowledgeNodeType.CANDIDATE
    assert node.attributes == {"name": "Daniel"}
    assert node.version == 2


def test_knowledge_node_type_covers_requested_knowledge_entities() -> None:
    """Every requested semantic entity has a stable node type."""
    assert set(KnowledgeNodeType) == {
        KnowledgeNodeType.CANDIDATE,
        KnowledgeNodeType.COMPANY,
        KnowledgeNodeType.JOB,
        KnowledgeNodeType.RESUME,
        KnowledgeNodeType.RESUME_VERSION,
        KnowledgeNodeType.SKILL,
        KnowledgeNodeType.CERTIFICATION,
        KnowledgeNodeType.LANGUAGE,
        KnowledgeNodeType.INTERVIEW,
        KnowledgeNodeType.PLATFORM,
        KnowledgeNodeType.CAREER_GOAL,
        KnowledgeNodeType.LEARNING,
        KnowledgeNodeType.DOCUMENT,
    }
