"""Structural validation for workflow business definitions."""

from __future__ import annotations

from dataclasses import dataclass

from acd.domain.workflow.workflow_definition import WorkflowDefinition
from acd.domain.workflow.workflow_stage import WorkflowStep


@dataclass(frozen=True)
class WorkflowValidationResult:
    """Represents the structural validation result of a workflow definition."""

    errors: tuple[str, ...] = ()

    @property
    def is_valid(self) -> bool:
        """Return whether no structural errors were found."""
        return not self.errors


class WorkflowValidator:
    """Validates workflow versions, graph integrity, and step identifiers."""

    def validate(self, definition: WorkflowDefinition) -> WorkflowValidationResult:
        """Validate a workflow definition without changing it."""
        step_ids = tuple(self._step_id(step) for step in definition.steps)
        errors: list[str] = []

        if not definition.version.strip():
            errors.append("Workflow version must not be empty.")
        if len(step_ids) != len(set(step_ids)):
            errors.append("Workflow contains duplicate step identifiers.")

        known_step_ids = set(step_ids)
        unknown_dependencies = self._unknown_dependencies(definition, known_step_ids)
        if unknown_dependencies:
            errors.append(f"Workflow contains unknown dependencies: {unknown_dependencies}.")

        if self._has_cycle(definition, known_step_ids):
            errors.append("Workflow dependencies contain a cycle.")
        if self._has_orphan_step(definition, step_ids):
            errors.append("Workflow contains an orphan step.")

        return WorkflowValidationResult(errors=tuple(errors))

    @staticmethod
    def _step_id(step: str | WorkflowStep) -> str:
        return step if isinstance(step, str) else step.step_id

    @staticmethod
    def _unknown_dependencies(
        definition: WorkflowDefinition, known_step_ids: set[str]
    ) -> tuple[str, ...]:
        unknown: set[str] = set()
        for step_id, dependencies in definition.dependencies.items():
            if step_id not in known_step_ids:
                unknown.add(step_id)
            unknown.update(dependency for dependency in dependencies if dependency not in known_step_ids)
        return tuple(sorted(unknown))

    def _has_cycle(self, definition: WorkflowDefinition, known_step_ids: set[str]) -> bool:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(step_id: str) -> bool:
            if step_id in visiting:
                return True
            if step_id in visited:
                return False

            visiting.add(step_id)
            for dependency in definition.dependencies.get(step_id, ()):
                if dependency in known_step_ids and visit(dependency):
                    return True
            visiting.remove(step_id)
            visited.add(step_id)
            return False

        return any(visit(step_id) for step_id in known_step_ids)

    @staticmethod
    def _has_orphan_step(definition: WorkflowDefinition, step_ids: tuple[str, ...]) -> bool:
        if len(step_ids) < 2:
            return False

        connected_steps = set(definition.dependencies)
        for dependencies in definition.dependencies.values():
            connected_steps.update(dependencies)
        return any(step_id not in connected_steps for step_id in step_ids)
