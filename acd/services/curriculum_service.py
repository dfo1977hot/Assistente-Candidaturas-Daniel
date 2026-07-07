from __future__ import annotations

from pathlib import Path

from acd.core.logger import logger
from acd.domain.entities.application import Application
from acd.domain.entities.curriculum import Curriculum
from acd.domain.entities.curriculum_version import CurriculumVersion
from acd.infrastructure.repositories.curriculum_repository import CurriculumRepository


class CurriculumService:
    """Serviço para gerenciamento de currículos e versões."""

    def __init__(self, repository: CurriculumRepository | None = None) -> None:
        self.repository = repository or CurriculumRepository()
        self.storage_root = Path("data/curriculos")
        self.storage_root.mkdir(parents=True, exist_ok=True)

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

    def delete_curriculum(self, curriculum_id: int) -> bool:
        """Remove um currículo."""
        deleted = self.repository.delete(curriculum_id)
        if deleted:
            logger.info("Currículo removido: %s", curriculum_id)
        return deleted

    def duplicate_curriculum(self, curriculum_id: int) -> Curriculum | None:
        """Cria uma nova versão a partir de um currículo existente."""
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
                file_name=base.name,
                file_path="",
                file_type="",
            ),
        )
        logger.info("Versão criada: %s", created.id)
        return created

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

    def import_curriculum(
        self, *, curriculum_id: int, file_name: str, file_bytes: bytes, file_type: str
    ) -> CurriculumVersion | None:
        """Importa um arquivo de currículo para o sistema de arquivos local."""
        curriculum = self.repository.get_by_id(curriculum_id)
        if curriculum is None:
            return None
        destination = self.storage_root / f"{curriculum_id}_{file_name}"
        destination.write_bytes(file_bytes)
        version = CurriculumVersion(
            curriculum_id=curriculum_id,
            version=curriculum.version,
            file_name=file_name,
            file_path=str(destination),
            file_type=file_type,
            checksum=self._checksum(file_bytes),
        )
        created_version = self.repository.create_version(curriculum_id, version)
        logger.info("Currículo importado: %s", created_version.id)
        return created_version

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
