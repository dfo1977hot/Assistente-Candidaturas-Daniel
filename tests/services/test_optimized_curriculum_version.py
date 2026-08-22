from __future__ import annotations

from types import SimpleNamespace

from acd.services.curriculum_service import CurriculumService


class _Repository:
    def __init__(self) -> None:
        self.source = SimpleNamespace(
            id=1,
            name="Currículo Logística",
            description="Conteúdo original",
            structured_content_json=None,
            version="V.1.0",
            language="pt-BR",
            is_default=True,
            status="Ativo",
            file_original_name=None,
            file_relative_path=None,
            file_extension=None,
        )
        self.items = [self.source]
        self.created_versions: list[object] = []

    def get_by_id(self, curriculum_id: int):
        return next((item for item in self.items if item.id == curriculum_id), None)

    def search(self, query: str):
        return [item for item in self.items if query.lower() in item.name.lower()]

    def create(self, curriculum):
        curriculum.id = len(self.items) + 1
        self.items.append(curriculum)
        return curriculum

    def create_version(self, curriculum_id: int, version):
        self.created_versions.append(version)
        return version


class _PromptRepository:
    def get_resume_versions(self, curriculum_id: int):
        assert curriculum_id == 1
        return [
            SimpleNamespace(
                version="v2.0",
                content="Conteúdo otimizado para a vaga",
                structured_content_json=None,
            )
        ]


class _DocumentService:
    def versioned_original_name(
        self,
        original_name: str,
        version: str,
    ) -> str:
        return f"{original_name}_{version}"

    def duplicate_document(self, source, created) -> None:
        raise AssertionError("Não deveria duplicar documento sem arquivo anexado")


def _service(repository: _Repository) -> CurriculumService:
    service = CurriculumService(
        repository=repository,
        prompt_repository=_PromptRepository(),
    )
    service.document_service = _DocumentService()
    return service


def test_create_optimized_curriculum_preserves_original_and_increments_version() -> None:
    repository = _Repository()
    service = _service(repository)

    created = service.create_optimized_curriculum(
        source_curriculum_id=1,
        generated_version="v2.0",
    )

    assert created is not None
    assert created.id == 2
    assert created.name == "Currículo Logística"
    assert created.version == "v2.0"
    assert created.description == "Conteúdo otimizado para a vaga"
    assert repository.source.description == "Conteúdo original"
    assert repository.source.version == "V.1.0"
    assert repository.created_versions[0].version == "v2.0"


def test_create_optimized_curriculum_is_idempotent_for_same_next_version() -> None:
    repository = _Repository()
    service = _service(repository)

    first = service.create_optimized_curriculum(
        source_curriculum_id=1,
        generated_version="v2.0",
    )
    second = service.create_optimized_curriculum(
        source_curriculum_id=1,
        generated_version="v2.0",
    )

    assert first is second
    assert len(repository.items) == 2
