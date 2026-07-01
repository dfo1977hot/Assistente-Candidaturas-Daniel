from acd.database.database import engine
from acd.models.base import Base

# importa os models
import acd.models.company
import acd.domain.entities.skill
import acd.domain.entities.certification
import acd.domain.entities.job
import acd.domain.entities.job_profile
import acd.domain.entities.curriculum
import acd.domain.entities.curriculum_version
import acd.domain.entities.application
import acd.domain.entities.ats_score
import acd.domain.entities.skill_gap
import acd.domain.entities.recommendation
import acd.domain.entities.score_detail
import acd.domain.entities.ai_prompt
import acd.domain.entities.ai_generation
import acd.domain.entities.resume_version
import acd.domain.entities.cover_letter_version
import acd.domain.entities.generation_log
import acd.domain.entities.prompt_template
import acd.domain.entities.automation_session
import acd.domain.entities.automation_log
import acd.domain.entities.automation_result
import acd.domain.entities.connector_setting
import acd.domain.entities.browser_profile
import acd.domain.entities.profile
import acd.domain.entities.experience
import acd.domain.entities.education
import acd.domain.entities.language
import acd.domain.entities.certification
import acd.domain.entities.project
import acd.domain.entities.publication
import acd.domain.entities.social_link
import acd.domain.entities.answer_template
import acd.domain.entities.profile_version
import acd.domain.connector.platform
import acd.domain.connector.schema
import acd.domain.connector.field_mapping
import acd.domain.connector.connector_profile
import acd.domain.connector.connector_rule
import acd.domain.connector.field_history
import acd.domain.entities.workflow
import acd.domain.entities.workflow_step
import acd.domain.entities.workflow_execution
import acd.domain.entities.workflow_event
import acd.domain.entities.workflow_log
import acd.domain.entities.workflow_template
import acd.domain.entities.metric
import acd.domain.entities.analytics_snapshot
import acd.domain.entities.report
import acd.domain.entities.analytics_recommendation
import acd.domain.entities.trend
import acd.domain.agent.agent_goal
import acd.domain.agent.execution_plan
import acd.domain.agent.reasoning_step
import acd.domain.agent.tool_call
import acd.domain.agents.agent
import acd.domain.agents.task
import acd.domain.agents.message
import acd.domain.agents.capability
import acd.domain.agents.tool
import acd.domain.agents.session
import acd.domain.agents.memory
import acd.domain.learning.learning_record
import acd.domain.learning.outcome
import acd.domain.learning.insight
import acd.domain.learning.pattern
import acd.domain.learning.hypothesis
import acd.domain.platform.health_report
import acd.domain.platform.system_status
import acd.domain.platform.system_log
import acd.domain.platform.system_metrics
import acd.domain.platform.backup
import acd.domain.platform.configuration
import acd.domain.release.release
import acd.domain.release.installed_version
import acd.domain.release.update_history
import acd.domain.release.migration_history
import acd.domain.release.documentation


def create_database():
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    create_database()
    print("Banco criado com sucesso.")