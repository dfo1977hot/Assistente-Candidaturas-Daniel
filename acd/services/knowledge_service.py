from __future__ import annotations

from typing import Protocol

from acd.core.logger import logger
from acd.domain.entities.skill import Skill, SkillAlias, SkillRelation
from acd.infrastructure.repositories.skill_repository import SkillRepository


class SkillClassifier(Protocol):
    """Interface para mecanismos de classificação."""

    def classify(self, skill_name: str) -> str: ...


class SimilarityEngine(Protocol):
    """Interface para mecanismos de comparação."""

    def calculate(self, left: str, right: str) -> float: ...


class RuleBasedSimilarityEngine:
    """Motor de similaridade baseado em regras configuráveis."""

    KNOWN_RELATIONS = {
        "lean": ["kaizen", "pdca", "six sigma", "dmaic"],
        "kaizen": ["lean", "pdca"],
        "six sigma": ["lean", "dmaic", "pdca"],
        "pdca": ["lean", "kaizen", "six sigma", "dmaic"],
        "dmaic": ["six sigma", "pdca"],
        "power bi": ["excel", "sql", "data"],
        "excel": ["power bi", "sql"],
        "sql": ["power bi", "excel"],
    }

    def __init__(self, *, alias_bonus: float = 0.25, word_bonus: float = 0.15) -> None:
        self.alias_bonus = alias_bonus
        self.word_bonus = word_bonus

    def calculate(self, left: str, right: str) -> float:
        normalized_left = left.lower().strip()
        normalized_right = right.lower().strip()
        if not normalized_left or not normalized_right:
            return 0.0
        if normalized_left == normalized_right:
            return 1.0
        if normalized_left in normalized_right or normalized_right in normalized_left:
            return 0.85
        if (
            normalized_left in self.KNOWN_RELATIONS
            and normalized_right in self.KNOWN_RELATIONS[normalized_left]
        ):
            return 0.6
        if (
            normalized_right in self.KNOWN_RELATIONS
            and normalized_left in self.KNOWN_RELATIONS[normalized_right]
        ):
            return 0.6
        shared_words = set(normalized_left.split()) & set(normalized_right.split())
        if shared_words:
            score = min(0.7, 0.3 + len(shared_words) * self.word_bonus)
            if len(shared_words) >= 2:
                score += self.alias_bonus
            return min(0.95, score)
        if any(word in normalized_right for word in normalized_left.split()) or any(
            word in normalized_left for word in normalized_right.split()
        ):
            return 0.45
        return 0.2


class RuleBasedClassifier:
    """Classificador simples baseado em palavras-chave."""

    CATEGORY_RULES = {
        "Produção": ["lean", "kaizen", "smed", "pdca", "mrp"],
        "Supply Chain": ["supply", "chain", "logistics", "planning"],
        "Logística": ["logistica", "transport", "warehouse"],
        "Qualidade": ["qualidade", "six sigma", "dmaic", "iso"],
        "Projetos": ["projeto", "scrum", "kanban", "agile"],
        "TI": ["power bi", "sql", "python", "excel", "sap", "oracle"],
        "Dados": ["dados", "data", "analytics", "bi"],
        "Gestão": ["gestao", "management", "lideranca"],
        "Liderança": ["lideranca", "leadership", "team"],
        "Financeiro": ["financeiro", "cost", "budget"],
        "Engenharia": ["engineering", "manufacturing"],
    }

    def classify(self, skill_name: str) -> str:
        lowered = skill_name.lower()
        for category, keywords in self.CATEGORY_RULES.items():
            if any(keyword in lowered for keyword in keywords):
                return category
        return "Geral"


class KnowledgeService:
    """Serviço de domínio para catalogar competências, relações e similaridades."""

    def __init__(
        self,
        repository: SkillRepository | None = None,
        classifier: SkillClassifier | None = None,
        similarity_engine: SimilarityEngine | None = None,
    ) -> None:
        self.repository = repository or SkillRepository()
        self.classifier = classifier or RuleBasedClassifier()
        self.similarity_engine = similarity_engine or RuleBasedSimilarityEngine()

    def create_skill(
        self,
        *,
        name: str,
        category: str = "",
        description: str = "",
        weight: float = 0.0,
    ) -> Skill:
        """Cria uma competência e persiste no catálogo."""
        cleaned_name = name.strip()
        if not cleaned_name:
            raise ValueError("Nome é obrigatório.")
        inferred_category = category or self.classifier.classify(cleaned_name)
        skill = Skill(
            name=cleaned_name,
            category=inferred_category,
            description=description.strip(),
            weight=weight,
            active=True,
        )
        created = self.repository.create(skill)
        logger.info("Competência criada: %s", created.name)
        return created

    def merge_skill(
        self, *, source_skill_id: int, target_skill_id: int, alias_name: str
    ) -> Skill | None:
        """Faz a fusão de uma competência com outra e registra um alias."""
        source = self.repository.get_by_id(source_skill_id)
        target = self.repository.get_by_id(target_skill_id)
        if source is None or target is None:
            return None
        self.repository.add_alias(target.id, alias_name.strip())
        logger.info("Competência fundida: %s -> %s", source.name, target.name)
        return target

    def update_skill(
        self,
        skill_id: int,
        *,
        name: str,
        category: str = "",
        description: str = "",
        weight: float = 0.0,
    ) -> Skill | None:
        """Atualiza uma competência existente."""
        skill = self.repository.get_by_id(skill_id)
        if skill is None:
            return None
        skill.name = name.strip()
        skill.category = category or skill.category or self.classifier.classify(name)
        skill.description = description.strip()
        skill.weight = weight
        return self.repository.update(skill)

    def delete_skill(self, skill_id: int) -> bool:
        """Remove uma competência."""
        return self.repository.delete(skill_id)

    def search_skills(self, query: str) -> list[Skill]:
        """Busca competências pelo nome."""
        return self.repository.search(query)

    def create_relation(
        self, *, parent_skill_id: int, child_skill_id: int, relation_type: str, strength: float
    ) -> SkillRelation | None:
        """Cria um relacionamento entre duas competências."""
        if parent_skill_id == child_skill_id:
            return None
        relation = SkillRelation(
            parent_skill_id=parent_skill_id,
            child_skill_id=child_skill_id,
            relation_type=relation_type,
            strength=strength,
        )
        created = self.repository.add_relation(relation)
        logger.info("Relacionamento criado: %s -> %s", parent_skill_id, child_skill_id)
        return created

    def calculate_similarity(self, left: str, right: str) -> float:
        """Calcula a similaridade entre duas competências."""
        return self.similarity_engine.calculate(left, right)

    def get_skill_tree(self) -> list[dict[str, object]]:
        """Retorna o catálogo simplificado para renderização de árvore."""
        return self.repository.get_tree()

    def get_aliases(self, skill_id: int) -> list[SkillAlias]:
        """Retorna os aliases de uma competência."""
        return self.repository.get_aliases(skill_id)

    def classify_skill(self, skill_name: str) -> str:
        """Classifica uma competência em uma categoria."""
        return self.classifier.classify(skill_name)

    def get_statistics(self) -> dict[str, int]:
        """Retorna estatísticas do catálogo para o dashboard."""
        return {
            "skills": self.repository.count(),
            "relations": self.repository.count_relations(),
            "categories": self.repository.count_categories(),
        }
