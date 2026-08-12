from __future__ import annotations

from types import SimpleNamespace

import pytest

from acd.resilience import CancellationToken, OperationCancelled
from acd.services.cover_letter_service import CoverLetterService


class Repository:
    def __init__(self) -> None:
        self.rows = []

    def get_all(self):
        return list(self.rows)

    def versions_for_context(self, *, job_id, curriculum_id):
        return [
            row
            for row in self.rows
            if row.job_id == job_id and row.curriculum_id == curriculum_id
        ]

    def latest_application_id_for_job(self, _job_id):
        return 31

    def create(self, entity):
        entity.id = len(self.rows) + 1
        self.rows.append(entity)
        return entity


class Responses:
    def create(self, **_values):
        return SimpleNamespace(output_text="Carta baseada apenas nos dados reais.")


@pytest.fixture
def service():
    repository = Repository()
    job = SimpleNamespace(
        id=10,
        company=SimpleNamespace(name="ACME"),
        title="Engenheiro Python",
        recruiter="Ana",
        recruiter_email="ana@example.com",
        notes="Python, SQL e APIs.",
    )
    curriculum = SimpleNamespace(
        id=20,
        name="Principal",
        version="V2.0",
        structured_content_json=None,
        description="Experiência real com Python e APIs.",
    )
    instance = CoverLetterService.__new__(CoverLetterService)
    instance.repository = repository
    instance.job_service = SimpleNamespace(get_job=lambda job_id: job if job_id == 10 else None)
    instance.curriculum_service = SimpleNamespace(
        repository=SimpleNamespace(
            get_by_id=lambda curriculum_id: curriculum if curriculum_id == 20 else None
        )
    )
    instance.settings_service = SimpleNamespace()
    instance._client = SimpleNamespace(responses=Responses())
    return instance


def generate(service, **extra):
    return service.generate_letter(
        job_id=10,
        curriculum_id=20,
        letter_type="Carta de Apresentação",
        language="Português",
        tone="Profissional",
        length="Média",
        **extra,
    )


def test_generation_reports_real_phases_and_reaches_100(service) -> None:
    progress = []
    letter = generate(service, progress=progress.append)
    assert letter.status == "Gerada"
    assert progress == [
        (5, "Preparando contexto"),
        (15, "Carregando vaga"),
        (25, "Carregando currículo"),
        (40, "Montando prompt"),
        (55, "Gerando conteúdo"),
        (75, "Validando resposta"),
        (90, "Salvando nova versão"),
        (100, "Concluído"),
    ]


def test_cancellation_before_persistence_creates_no_version(service) -> None:
    token = CancellationToken()

    def cancel_before_save(update):
        if update[0] == 90:
            token.request_cancellation()

    with pytest.raises(OperationCancelled):
        generate(service, progress=cancel_before_save, cancellation=token)
    assert service.repository.rows == []


def test_consecutive_generations_create_distinct_versions(service) -> None:
    first = generate(service)
    second = generate(service)
    third = generate(service)
    assert [first.version, second.version, third.version] == ["V1.0", "V1.1", "V1.2"]
    assert len(service.repository.rows) == 3


def test_missing_job_or_curriculum_blocks_before_generation(service) -> None:
    with pytest.raises(ValueError, match="vaga válida"):
        service.generate_letter(
            job_id=99,
            curriculum_id=20,
            letter_type="Carta de Apresentação",
            language="Português",
            tone="Profissional",
            length="Média",
        )
    with pytest.raises(ValueError, match="currículo válido"):
        service.generate_letter(
            job_id=10,
            curriculum_id=99,
            letter_type="Carta de Apresentação",
            language="Português",
            tone="Profissional",
            length="Média",
        )


def test_prompt_explicitly_forbids_invented_professional_facts(service) -> None:
    context = service.build_context(job_id=10, curriculum_id=20)
    prompt = service._build_prompt(
        context=context,
        letter_type="Carta de Apresentação",
        language="Português",
        tone="Profissional",
        length="Média",
    )
    assert "Não invente experiências, resultados, competências, nomes ou números" in prompt
    assert "Use apenas informações existentes no contexto" in prompt
