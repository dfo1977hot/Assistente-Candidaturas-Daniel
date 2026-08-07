from __future__ import annotations

from acd.domain.workflow.workflow_catalog import WorkflowCatalog
from acd.domain.workflow.workflow_definition import WorkflowCategory
from acd.domain.workflow.workflow_validation import WorkflowValidator


def test_workflow_catalog_registers_all_initial_business_workflows() -> None:
    """The default catalog exposes one workflow for each requested business process."""
    registry = WorkflowCatalog.create_default_registry()

    assert {definition.category for definition in registry.list_all()} == {
        WorkflowCategory.APPLICATION,
        WorkflowCategory.INTERVIEW,
        WorkflowCategory.CAREER,
        WorkflowCategory.RESUME,
        WorkflowCategory.ATS,
    }


def test_workflow_catalog_definitions_are_structurally_valid() -> None:
    """Initial catalog definitions satisfy the workflow structural rules."""
    validator = WorkflowValidator()

    assert all(validator.validate(definition).is_valid for definition in WorkflowCatalog.definitions())
