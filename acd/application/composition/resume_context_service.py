"""Resume context composition service."""

from __future__ import annotations

from acd.application.composition.ats_context_adapter import ATSContextAdapter
from acd.application.composition.read_models import ATSContext, GapContext, ResumeContext
from acd.application.query_ports import ATSHistoryQueryDTO, ATSHistoryQueryPort, ResumeQueryPort


class ResumeContextService:
    """Composes resume and persisted ATS read models through Query Ports."""

    def __init__(
        self,
        resume_query_port: ResumeQueryPort,
        ats_history_query_port: ATSHistoryQueryPort,
        ats_context_adapter: ATSContextAdapter,
    ) -> None:
        self._resume_query_port = resume_query_port
        self._ats_history_query_port = ats_history_query_port
        self._ats_context_adapter = ats_context_adapter

    def build(self, curriculum_id: int) -> ResumeContext | None:
        """Return a read-only context for an existing curriculum."""
        resume = self._resume_query_port.get_by_id(curriculum_id)
        if resume is None:
            return None
        return ResumeContext(
            curriculum_id=resume.curriculum_id,
            version=resume.version,
            description=resume.description,
            structured_resume=resume.structured_resume,
        )

    def get_ats_context(self, curriculum_id: int) -> ATSContext | None:
        """Return the available persisted ATS result for a curriculum."""
        history = self.get_persisted_ats_result(curriculum_id)
        if history is None:
            return None
        return self._ats_context_adapter.from_history(history)

    def get_persisted_ats_result(self, curriculum_id: int) -> ATSHistoryQueryDTO | None:
        """Return the latest persisted ATS analysis without executing a command."""
        return self._ats_history_query_port.get_latest_for_curriculum(curriculum_id)

    def get_gap_context(self, curriculum_id: int) -> GapContext | None:
        """Return persisted ATS gaps without treating missing data as no gaps."""
        history = self.get_persisted_ats_result(curriculum_id)
        if history is None:
            return None
        return self._ats_context_adapter.gap_context_from_history(history)
