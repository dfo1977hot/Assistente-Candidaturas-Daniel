"""Interview context composition service."""

from __future__ import annotations

from acd.application.composition.application_context_service import ApplicationContextService
from acd.application.composition.read_models import CompanyContext, InterviewContext, VacancyContext
from acd.application.composition.resume_context_service import ResumeContextService
from acd.application.query_ports import (
    ApplicationQueryPort,
    CompanyQueryPort,
    InterviewQueryPort,
    VacancyQueryPort,
)


class InterviewContextService:
    """Composes interview context from existing read-only query contracts."""

    def __init__(
        self,
        application_query_port: ApplicationQueryPort,
        application_context_service: ApplicationContextService,
        resume_context_service: ResumeContextService,
        company_query_port: CompanyQueryPort,
        vacancy_query_port: VacancyQueryPort,
        interview_query_port: InterviewQueryPort,
    ) -> None:
        self._application_query_port = application_query_port
        self._application_context_service = application_context_service
        self._resume_context_service = resume_context_service
        self._company_query_port = company_query_port
        self._vacancy_query_port = vacancy_query_port
        self._interview_query_port = interview_query_port

    def build(self, application_id: int) -> InterviewContext | None:
        """Return complete read-only context for an existing application."""
        application = self._application_query_port.get_by_id(application_id)
        context = self._application_context_service.build(application_id)
        if application is None or context is None:
            return None

        company = self._company_query_port.get_by_id(application.company_id)
        vacancy = self._vacancy_query_port.get_by_id(application.job_id)
        if company is None or vacancy is None:
            return None

        resume = (
            None
            if application.curriculum_id is None
            else self._resume_context_service.build(application.curriculum_id)
        )
        ats_result = (
            None
            if application.curriculum_id is None
            else self._resume_context_service.get_ats_context(application.curriculum_id)
        )
        gaps = (
            None
            if application.curriculum_id is None
            else self._resume_context_service.get_gap_context(application.curriculum_id)
        )
        return InterviewContext(
            application=context,
            vacancy=VacancyContext(
                job_id=vacancy.job_id,
                title=vacancy.title,
                competencies=vacancy.competencies,
            ),
            company=CompanyContext(
                company_id=company.company_id,
                name=company.name,
                segment=company.segment,
            ),
            resume=resume,
            identified_competencies=vacancy.competencies,
            ats_result=ats_result,
            gaps=gaps,
            related_history=tuple(
                {
                    "interview_id": interview.interview_id,
                    "interview_date": interview.interview_date.isoformat(),
                    "interview_type": interview.interview_type,
                    "result": interview.result,
                }
                for interview in self._interview_query_port.list_by_application(application_id)
            ),
        )
