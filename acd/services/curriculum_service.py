from __future__ import annotations

from pathlib import Path

from acd.core.logger import logger
from acd.domain.entities.application import Application
from acd.domain.entities.curriculum import Curriculum
from acd.domain.entities.curriculum_version import CurriculumVersion
from acd.infrastructure.repositories.curriculum_repository import CurriculumRepository
from acd.services.curriculum_document_service import CurriculumDocumentService


class CurriculumService:
    """Serviço para gerenciamento de currículos e versões."""

    def __init__(self, repository: CurriculumRepository | None = None) -> None:
        self.repository = repository or CurriculumRepository()
        self.storage_root = Path("data/curriculos")
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.document_service = CurriculumDocumentService(self.repository)

    def create_curriculum(
        self, *, name: str, version: str = "v1.0", language: str = "pt-BR", description: str = ""
    ) -> Curriculum:
        """Cria um currículo e sua primeira versão."""
        curriculum = Curriculum(
            name=name.strip(),
            version=version.strip(),
            language=language.strip(),
            description=description.strip(),
        )
        created = self.repository.create(curriculum)
        self.repository.create_version(
            created.id,
            CurriculumVersion(
                curriculum_id=created.id,
                version=version.strip(),
                file_name="",
                file_path="",
                file_type="",
            ),
        )
        logger.info("Currículo criado: %s", created.id)
        return created

    def update_curriculum(
        self, curriculum_id: int, *, name: str, version: str, language: str, description: str = ""
    ) -> Curriculum | None:
        """Atualiza um currículo."""
        curriculum = self.repository.get_by_id(curriculum_id)
        if curriculum is None:
            return None
        curriculum.name = name.strip()
        curriculum.version = version.strip()
        curriculum.language = language.strip()
        curriculum.description = description.strip()
        updated = self.repository.update(curriculum)
        logger.info("Currículo atualizado: %s", updated.id)
        return updated

    def delete_curriculum(self, curriculum_id: int, *, delete_linked: bool = False) -> bool:
        """Remove um currículo e seu arquivo após a confirmação no banco."""
        curriculum = self.repository.get_by_id(curriculum_id)
        document_path = (
            self.document_service.resolve_path(curriculum.file_relative_path)
            if curriculum is not None
            else None
        )
        deleted = self.repository.delete(curriculum_id, delete_linked=delete_linked)
        if deleted:
            if document_path:
                document_path.unlink(missing_ok=True)
            logger.info("Currículo removido: %s", curriculum_id)
        return deleted

    def duplicate_curriculum(self, curriculum_id: int) -> Curriculum | None:
        """Cria nova versão e duplica o arquivo físico quando disponível."""
        base = self.repository.get_by_id(curriculum_id)
        if base is None:
            return None
        next_version = self._next_version(base.version)
        duplicated = Curriculum(
            name=base.name,
            description=base.description,
            version=next_version,
            language=base.language,
            is_default=False,
        )
        created = self.repository.create(duplicated)
        self.repository.create_version(
            created.id,
            CurriculumVersion(
                curriculum_id=created.id,
                version=next_version,
                file_name=base.file_original_name or base.name,
                file_path="",
                file_type=(base.file_extension or "").removeprefix("."),
            ),
        )
        if base.file_relative_path:
            self.document_service.duplicate_document(base, created)
            created = self.repository.get_by_id(created.id) or created
        logger.info("Versão criada: %s", created.id)
        return created

    def attach_document(self, curriculum_id: int, source_path: str | Path) -> Curriculum:
        return self.document_service.attach_document(curriculum_id, source_path)

    def remove_document(self, curriculum_id: int) -> Curriculum:
        return self.document_service.remove_document(curriculum_id)

    def open_document(self, curriculum_id: int) -> None:
        self.document_service.open_document(curriculum_id)

    def activate_curriculum(self, curriculum_id: int) -> Curriculum | None:
        """Marca um currículo como padrão."""
        curriculum = self.repository.get_by_id(curriculum_id)
        if curriculum is None:
            return None
        current_default = self.repository.get_default()
        if current_default is not None and current_default.id != curriculum_id:
            current_default.is_default = False
            self.repository.update(current_default)
        curriculum.is_default = True
        updated = self.repository.update(curriculum)
        logger.info("Currículo ativado: %s", updated.id)
        return updated

    def associate_to_application(
        self, *, application_id: int, curriculum_id: int
    ) -> Application | None:
        """Associa um currículo a uma candidatura."""
        application = self._get_application(application_id)
        if application is None:
            return None
        curriculum = self.repository.get_by_id(curriculum_id)
        if curriculum is None:
            return None
        application.curriculum_id = curriculum_id
        application.curriculum_version = curriculum.version
        self._save_application(application)
        logger.info("Currículo associado à candidatura: %s", application_id)
        return application

    def search_curricula(self, query: str) -> list[Curriculum]:
        """Pesquisa currículos."""
        return self.repository.search(query)

    def get_versions(self, curriculum_id: int) -> list[CurriculumVersion]:
        """Retorna versões de um currículo."""
        return self.repository.get_versions(curriculum_id)

    def get_statistics(self) -> dict[str, int]:
        """Retorna estatísticas básicas."""
        from acd.infrastructure.repositories.application_repository import ApplicationRepository

        repo = ApplicationRepository()
        applications = repo.get_all()
        used = sum(1 for application in applications if getattr(application, "curriculum_id", None))
        return {
            "total": len(self.repository.get_all()),
            "versions": len(self.repository.get_all()) * 2,
            "used": used,
        }

    def _next_version(self, version: str) -> str:
        base = version.replace("v", "")
        if "." in base:
            major, minor = base.split(".", 1)
            return f"v{major}.{int(minor) + 1}"
        return f"v{base}.1"

    def _checksum(self, data: bytes) -> str:
        import hashlib

        return hashlib.sha256(data).hexdigest()

    def _get_application(self, application_id: int) -> Application | None:
        from acd.infrastructure.repositories.application_repository import ApplicationRepository

        return ApplicationRepository().get_by_id(application_id)

    def _save_application(self, application: Application) -> None:
        from acd.infrastructure.repositories.application_repository import ApplicationRepository

        ApplicationRepository().update(application)
