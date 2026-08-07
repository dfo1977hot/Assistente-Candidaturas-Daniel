"""Deterministic registration of the productive SQLAlchemy models."""
from __future__ import annotations

from dataclasses import dataclass
import importlib

from acd.models.base import Base

_GROUPS = {
 "agent":"agent_goal execution_plan plan_task reasoning_step tool_call", "agents":"agent capability memory message session task tool",
 "career":"career_goal career_recommendation development_plan milestone skill_gap", "connector":"connector_profile connector_rule field_history field_mapping platform schema",
 "learning":"hypothesis insight learning_record outcome pattern", "platform":"backup configuration health_report system_log system_metrics system_status", "release":"documentation installed_version migration_history release update_history",
 "entities":"ai_generation ai_prompt analytics_recommendation analytics_snapshot answer_template application ats_score automation_log automation_result automation_session browser_profile certification connector_setting cover_letter_version curriculum curriculum_version education experience generation_log interview job job_profile keyword language metric pipeline_execution profile profile_version project prompt_template publication recommendation report resume_version score_detail skill skill_gap social_link timeline_event trend workflow workflow_event workflow_execution workflow_log workflow_step workflow_template",
}
ORM_MODEL_MODULES = tuple(f"acd.domain.{group}.{name}" for group, names in _GROUPS.items() for name in names.split())
EXPECTED_ORM_TABLES = frozenset("agent_capabilities agent_goals agent_memory agent_messages agent_sessions agent_tools agents ai_generations ai_prompts analytics_recommendations analytics_snapshots answer_templates applications ats_scores automation_logs automation_results automation_sessions browser_profiles career_goals career_recommendations career_skill_gaps categories certifications companies connector_profiles connector_rules connector_settings cover_letter_versions curricula curriculum_versions development_plans documentation_topics educations execution_plans experiences feature_flags field_history field_mappings generation_logs health_reports hypotheses insights installation_logs installed_versions interviews job_profiles jobs keywords languages learning_records metrics migration_history milestones multi_agent_tasks outcomes patterns pipeline_executions plan_tasks platform_schemas platforms profile_versions profiles projects prompt_templates publications reasoning_steps recommendations reports resume_versions score_details skill_aliases skill_gaps skill_relations skill_weights skills social_links system_backups system_logs system_metrics system_releases system_settings system_status timeline_events tool_calls trends update_history workflow_events workflow_executions workflow_logs workflow_steps workflow_templates workflows".split())

class ModelRegistryError(RuntimeError):
    """Raised when explicit ORM model loading or validation fails."""

@dataclass(frozen=True, slots=True)
class ModelRegistryResult:
    loaded_modules: tuple[str, ...]
    registered_tables: tuple[str, ...]
    missing_tables: tuple[str, ...]
    unexpected_tables: tuple[str, ...]

def load_models() -> ModelRegistryResult:
    for module in ORM_MODEL_MODULES:
        try:
            importlib.import_module(module)
        except Exception as exc:
            raise ModelRegistryError(f"ORM model import failed: {module}") from exc
    actual = frozenset(Base.metadata.tables)
    missing, unexpected = EXPECTED_ORM_TABLES - actual, actual - EXPECTED_ORM_TABLES
    if missing or unexpected:
        raise ModelRegistryError(f"ORM registry mismatch: missing={sorted(missing)} unexpected={sorted(unexpected)} expected_count={len(EXPECTED_ORM_TABLES)} actual_count={len(actual)}")
    return ModelRegistryResult(ORM_MODEL_MODULES, tuple(sorted(actual)), tuple(), tuple())
