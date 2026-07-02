import pytest

from acd.presentation.pages.agent_console_page import AgentConsolePage
from acd.presentation.pages.ai_resume_page import AIResumePage
from acd.presentation.pages.analytics_page import AnalyticsPage
from acd.presentation.pages.application_page import ApplicationPage
from acd.presentation.pages.assistant_page import AssistantPage
from acd.presentation.pages.ats_page import ATSPage
from acd.presentation.pages.automation_page import AutomationPage
from acd.presentation.pages.career_page import CareerPage
from acd.presentation.pages.company_page import CompanyPage
from acd.presentation.pages.curriculum_page import CurriculumPage
from acd.presentation.pages.interview_page import InterviewPage
from acd.presentation.pages.job_page import JobPage
from acd.presentation.pages.knowledge_page import KnowledgePage
from acd.presentation.pages.workflow_page import WorkflowPage


@pytest.mark.parametrize(
    "page_cls",
    [
        CompanyPage,
        JobPage,
        ApplicationPage,
        InterviewPage,
        CurriculumPage,
        WorkflowPage,
        AnalyticsPage,
        CareerPage,
        AssistantPage,
        AgentConsolePage,
        AIResumePage,
        ATSPage,
        AutomationPage,
        KnowledgePage,
    ],
)
def test_pages_initialize(page_cls, qapp):
    page = page_cls()

    assert page is not None
    assert hasattr(page, "layout")
