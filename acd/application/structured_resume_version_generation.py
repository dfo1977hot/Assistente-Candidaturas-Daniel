"""Application use case for generating and persisting structured resume versions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from acd.application.resume_optimization.resume_optimization_workflow import (
    ResumeOptimizationAvailability,
    ResumeOptimizationWorkflow,
)
from acd.application.structured_resume_generation import (
    StructuredResumeGenerationPort,
    StructuredResumeProviderRequest,
    StructuredResumeProviderStatus,
    validate_structured_generation_eligibility,
)
from acd.application.structured_resume_snapshot import (
    StructuredResumeSnapshot,
    StructuredResumeSnapshotCodec,
    StructuredResumeValidationError,
)


class StructuredResumeVersionGenerationStatus(StrEnum):
    """Functional outcomes of one explicit structured generation request."""

    SUCCESS = "success"
    APPLICATION_NOT_FOUND = "application_not_found"
    CURRICULUM_REQUIRED = "curriculum_required"
    ATS_REQUIRED = "ats_required"
    VACANCY_REQUIRED = "vacancy_required"
    STRUCTURED_SOURCE_REQUIRED = "structured_source_required"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    PROVIDER_CONFIGURATION_REQUIRED = "provider_configuration_required"
    PROVIDER_TIMEOUT = "provider_timeout"
    PROVIDER_RESPONSE_INVALID = "provider_response_invalid"
    UNSUPPORTED_SCHEMA = "unsupported_schema"
    GENERATION_FAILED = "generation_failed"
    PERSISTENCE_FAILED = "persistence_failed"


@dataclass(frozen=True)
class GenerateStructuredResumeVersionRequest:
    """Explicit intent to generate one version from an application's original curriculum."""

    application_id: int
    optimization_guidance: str | None = None


@dataclass(frozen=True)
class GenerateStructuredResumeVersionResult:
    """Application-safe outcome with no provider or persistence implementation details."""

    status: StructuredResumeVersionGenerationStatus
    application_id: int
    curriculum_id: int | None = None
    resume_version_id: int | None = None
    version: str | None = None
    explanation: str | None = None
    source_schema_version: int | None = None
    message: str = ""


@dataclass(frozen=True)
class CreateStructuredResumeVersionRequest:
    """Validated data that must be stored atomically as one resume version."""

    curriculum_id: int
    content: str
    structured_resume: StructuredResumeSnapshot
    explanation: str


@dataclass(frozen=True)
class CreatedStructuredResumeVersion:
    """Minimal immutable record returned after one successful atomic write."""

    resume_version_id: int
    version: str


class StructuredResumeVersionWritePort(Protocol):
    """Application-safe transaction boundary for structured resume versions."""

    def create_structured_resume_version(
        self, request: CreateStructuredResumeVersionRequest
    ) -> CreatedStructuredResumeVersion:
        """Persist all representations or none of them."""


class StructuredResumeTextRenderer:
    """Pure deterministic renderer for the schema-v1 snapshot."""

    def render(self, snapshot: StructuredResumeSnapshot) -> str:
        """Render only populated snapshot fields in their original order."""
        blocks: list[str] = []
        identity = [
            value
            for value in (snapshot.identity.full_name, snapshot.identity.professional_title, snapshot.identity.location)
            if value
        ]
        if identity:
            blocks.append("\n".join(identity))
        contact = [value for value in vars(snapshot.contact).values() if value]
        if contact:
            blocks.append(" | ".join(contact))
        self._section(blocks, "RESUMO PROFISSIONAL", [snapshot.summary] if snapshot.summary else [])
        self._section(blocks, "COMPETÊNCIAS", list(snapshot.skills))
        experiences = []
        for item in snapshot.experiences:
            heading = " — ".join(value for value in (item.role, item.company) if value)
            period = " | ".join(value for value in (item.location, item.start_date, item.end_date) if value)
            values = [value for value in (heading, period, item.summary) if value]
            values.extend(f"• {achievement}" for achievement in item.achievements)
            if values:
                experiences.append("\n".join(values))
        self._section(blocks, "EXPERIÊNCIA PROFISSIONAL", experiences)
        self._section(blocks, "FORMAÇÃO ACADÊMICA", [self._join_fields(item.institution, item.degree, item.field, item.start_date, item.end_date, item.status, item.details) for item in snapshot.education])
        self._section(blocks, "CERTIFICAÇÕES", [self._join_fields(item.name, item.issuer, item.issued_date, item.credential_id, item.url) for item in snapshot.certifications])
        self._section(blocks, "CURSOS", [self._join_fields(item.name, item.provider, item.completed_date, item.details) for item in snapshot.courses])
        self._section(blocks, "IDIOMAS", [self._join_fields(item.name, item.proficiency) for item in snapshot.languages])
        self._section(blocks, "PROJETOS", [self._join_fields(item.name, item.description, item.url, *item.highlights) for item in snapshot.projects])
        for item in snapshot.additional_sections:
            self._section(blocks, item.title, [*item.paragraphs, *item.items])
        return "\n\n".join(blocks)

    @staticmethod
    def _section(blocks: list[str], title: str | None, values: list[str]) -> None:
        content = [value for value in values if value]
        if title and content:
            blocks.append(f"{title}\n\n" + "\n\n".join(content))

    @staticmethod
    def _join_fields(*values: str | None) -> str:
        return " | ".join(value for value in values if value)


class GenerateStructuredResumeVersionUseCase:
    """Generate from the original curriculum snapshot without automatic adoption."""

    def __init__(
        self,
        workflow: ResumeOptimizationWorkflow,
        provider: StructuredResumeGenerationPort,
        renderer: StructuredResumeTextRenderer,
        write_port: StructuredResumeVersionWritePort,
        codec: StructuredResumeSnapshotCodec | None = None,
    ) -> None:
        self._workflow = workflow
        self._provider = provider
        self._renderer = renderer
        self._write_port = write_port
        self._codec = codec or StructuredResumeSnapshotCodec()

    def execute(
        self, request: GenerateStructuredResumeVersionRequest
    ) -> GenerateStructuredResumeVersionResult:
        """Generate, render, and persist one structured version in the write boundary."""
        preparation = self._workflow.execute(request.application_id)
        unavailable = self._availability_result(preparation.availability, request.application_id, preparation.curriculum_id)
        if unavailable is not None:
            return unavailable
        assert preparation.resume is not None and preparation.vacancy is not None
        assert preparation.curriculum_id is not None
        eligibility = validate_structured_generation_eligibility(
            preparation.resume.structured_resume, self._provider.get_capabilities()
        )
        if eligibility is not StructuredResumeProviderStatus.SUCCESS:
            return self._provider_status_result(eligibility, request.application_id, preparation.curriculum_id)
        assert preparation.resume.structured_resume is not None
        result = self._provider.generate_structured_resume(
            StructuredResumeProviderRequest(
                preparation.resume.structured_resume,
                preparation.vacancy,
                (() if request.optimization_guidance is None else (request.optimization_guidance,)),
            )
        )
        if result.status is not StructuredResumeProviderStatus.SUCCESS or result.structured_resume is None:
            return self._provider_status_result(result.status, request.application_id, preparation.curriculum_id, result.message)
        try:
            snapshot = self._codec.loads(self._codec.dumps(result.structured_resume))
        except (StructuredResumeValidationError, ValueError):
            return self._result(StructuredResumeVersionGenerationStatus.PROVIDER_RESPONSE_INVALID, request.application_id, preparation.curriculum_id)
        try:
            content = self._renderer.render(snapshot)
        except Exception:
            return self._result(StructuredResumeVersionGenerationStatus.GENERATION_FAILED, request.application_id, preparation.curriculum_id)
        try:
            created = self._write_port.create_structured_resume_version(
                CreateStructuredResumeVersionRequest(
                    preparation.curriculum_id,
                    content,
                    snapshot,
                    result.explanation or "",
                )
            )
        except Exception:
            return self._result(StructuredResumeVersionGenerationStatus.PERSISTENCE_FAILED, request.application_id, preparation.curriculum_id)
        return GenerateStructuredResumeVersionResult(
            StructuredResumeVersionGenerationStatus.SUCCESS, request.application_id,
            preparation.curriculum_id, created.resume_version_id, created.version,
            result.explanation, snapshot.schema_version,
        )

    def _availability_result(self, availability: ResumeOptimizationAvailability, application_id: int, curriculum_id: int | None) -> GenerateStructuredResumeVersionResult | None:
        mapping = {
            ResumeOptimizationAvailability.APPLICATION_NOT_FOUND: StructuredResumeVersionGenerationStatus.APPLICATION_NOT_FOUND,
            ResumeOptimizationAvailability.CURRICULUM_REQUIRED: StructuredResumeVersionGenerationStatus.CURRICULUM_REQUIRED,
            ResumeOptimizationAvailability.ATS_REQUIRED: StructuredResumeVersionGenerationStatus.ATS_REQUIRED,
            ResumeOptimizationAvailability.VACANCY_REQUIRED: StructuredResumeVersionGenerationStatus.VACANCY_REQUIRED,
        }
        status = mapping.get(availability)
        return None if status is None else self._result(status, application_id, curriculum_id)

    def _provider_status_result(self, status: StructuredResumeProviderStatus, application_id: int, curriculum_id: int, message: str = "") -> GenerateStructuredResumeVersionResult:
        mapping = {
            StructuredResumeProviderStatus.STRUCTURED_SOURCE_REQUIRED: StructuredResumeVersionGenerationStatus.STRUCTURED_SOURCE_REQUIRED,
            StructuredResumeProviderStatus.UNSUPPORTED: StructuredResumeVersionGenerationStatus.PROVIDER_UNAVAILABLE,
            StructuredResumeProviderStatus.CONFIGURATION_REQUIRED: StructuredResumeVersionGenerationStatus.PROVIDER_CONFIGURATION_REQUIRED,
            StructuredResumeProviderStatus.TIMEOUT: StructuredResumeVersionGenerationStatus.PROVIDER_TIMEOUT,
            StructuredResumeProviderStatus.INVALID_RESPONSE: StructuredResumeVersionGenerationStatus.PROVIDER_RESPONSE_INVALID,
            StructuredResumeProviderStatus.UNSUPPORTED_SCHEMA: StructuredResumeVersionGenerationStatus.UNSUPPORTED_SCHEMA,
        }
        return self._result(mapping.get(status, StructuredResumeVersionGenerationStatus.GENERATION_FAILED), application_id, curriculum_id, message)

    @staticmethod
    def _result(status: StructuredResumeVersionGenerationStatus, application_id: int, curriculum_id: int | None, message: str = "") -> GenerateStructuredResumeVersionResult:
        return GenerateStructuredResumeVersionResult(status, application_id, curriculum_id, message=message)
