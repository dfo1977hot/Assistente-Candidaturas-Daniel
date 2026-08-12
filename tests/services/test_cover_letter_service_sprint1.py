from types import SimpleNamespace

from acd.services.cover_letter_service import CoverLetterService


class Repository:
    def __init__(self):
        self.rows = []

    def versions_for_context(self, *, job_id, curriculum_id):
        return [
            SimpleNamespace(version="V1.0"),
            SimpleNamespace(version="V1.1"),
        ]

    def latest_application_id_for_job(self, job_id):
        return 7


def test_next_version_never_overwrites_previous_generation() -> None:
    service = CoverLetterService.__new__(CoverLetterService)
    service.repository = Repository()
    assert service.next_version(job_id=10, curriculum_id=20) == "V1.2"


def test_letter_catalogs_are_available() -> None:
    assert "Carta de Apresentação" in CoverLetterService.LETTER_TYPES
    assert "Português" in CoverLetterService.LANGUAGES
    assert "Profissional" in CoverLetterService.TONES
    assert "Gerada" in CoverLetterService.STATUSES
