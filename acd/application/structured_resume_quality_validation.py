"""Deterministic, read-only quality validation for structured resumes."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
import re

from acd.application.application_resume_source import ApplicationResumeSource
from acd.application.effective_application_resume_use_case import (
    EffectiveApplicationResumeRequest,
    EffectiveApplicationResumeStatus,
    EffectiveApplicationResumeUseCase,
)
from acd.application.structured_resume_snapshot import (
    StructuredResumeContentStatus,
    StructuredResumeSnapshot,
)


class StructuredResumeQualitySeverity(StrEnum):
    """Severity assigned to a deterministic structural quality issue."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class StructuredResumeQualityCategory(StrEnum):
    """Categories covered by the initial structural validation rules."""

    IDENTITY = "identity"
    CONTACT = "contact"
    SKILLS = "skills"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    CERTIFICATIONS = "certifications"
    LANGUAGES = "languages"
    CHRONOLOGY = "chronology"
    DUPLICATION = "duplication"
    CONSISTENCY = "consistency"
    EXPORTABILITY = "exportability"
    STRUCTURE = "structure"


class EffectiveStructuredResumeQualityStatus(StrEnum):
    """Functional outcomes of effective structured resume validation."""

    SUCCESS = "success"
    APPLICATION_NOT_FOUND = "application_not_found"
    CURRICULUM_NOT_FOUND = "curriculum_not_found"
    ADOPTED_RESUME_VERSION_NOT_FOUND = "adopted_resume_version_not_found"
    STRUCTURED_CONTENT_REQUIRED = "structured_content_required"
    UNSUPPORTED_SCHEMA = "unsupported_schema"
    VALIDATION_FAILED = "validation_failed"


@dataclass(frozen=True)
class StructuredResumeQualityIssue:
    """A stable, non-sensitive structural quality finding."""

    code: str
    severity: StructuredResumeQualitySeverity
    category: StructuredResumeQualityCategory
    section: str
    field: str
    message: str
    recommendation: str


@dataclass(frozen=True)
class StructuredResumeQualityValidation:
    """Immutable, internally consistent result from the pure validator."""

    issues: tuple[StructuredResumeQualityIssue, ...] = ()
    is_valid: bool = field(init=False)
    score: int = field(init=False)
    error_count: int = field(init=False)
    warning_count: int = field(init=False)
    info_count: int = field(init=False)

    def __post_init__(self) -> None:
        ordered = tuple(sorted(self.issues, key=_issue_sort_key))
        object.__setattr__(self, "issues", ordered)
        errors = sum(issue.severity is StructuredResumeQualitySeverity.ERROR for issue in ordered)
        warnings = sum(issue.severity is StructuredResumeQualitySeverity.WARNING for issue in ordered)
        infos = sum(issue.severity is StructuredResumeQualitySeverity.INFO for issue in ordered)
        object.__setattr__(self, "error_count", errors)
        object.__setattr__(self, "warning_count", warnings)
        object.__setattr__(self, "info_count", infos)
        object.__setattr__(self, "is_valid", errors == 0)
        object.__setattr__(self, "score", max(0, min(100, 100 - errors * 20 - warnings * 5 - infos)))


@dataclass(frozen=True)
class ValidateEffectiveStructuredResumeQualityRequest:
    """Request validation for the resume effectively selected by one application."""

    application_id: int


@dataclass(frozen=True)
class ValidateEffectiveStructuredResumeQualityResult:
    """Application-safe, read-only validation outcome."""

    status: EffectiveStructuredResumeQualityStatus
    application_id: int
    source: ApplicationResumeSource = ApplicationResumeSource.ORIGINAL
    curriculum_id: int | None = None
    resume_version_id: int | None = None
    is_valid: bool = False
    score: int = 0
    issues: tuple[StructuredResumeQualityIssue, ...] = ()
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    summary: str = ""
    message: str = ""


class StructuredResumeQualityValidator:
    """Apply deterministic structural quality rules without changing a snapshot."""

    _PLACEHOLDERS = frozenset(
        {
            "lorem ipsum",
            "todo",
            "preencher depois",
            "completar depois",
            "texto de exemplo",
            "placeholder",
            "n/a",
            "insira aqui",
        }
    )

    def validate(self, snapshot: StructuredResumeSnapshot) -> StructuredResumeQualityValidation:
        """Return structural findings for a snapshot without mutating it."""
        issues: list[StructuredResumeQualityIssue] = []
        self._validate_identity(snapshot, issues)
        self._validate_contact(snapshot, issues)
        self._validate_skills(snapshot, issues)
        self._validate_experiences(snapshot, issues)
        self._validate_duplicates(snapshot, issues)
        self._validate_content(snapshot, issues)
        self._validate_exportability(snapshot, issues)
        return StructuredResumeQualityValidation(tuple(issues))

    def _validate_identity(self, snapshot: StructuredResumeSnapshot, issues: list[StructuredResumeQualityIssue]) -> None:
        if _empty(snapshot.identity.full_name):
            issues.append(_issue("IDENTITY_NAME_REQUIRED", StructuredResumeQualitySeverity.ERROR, StructuredResumeQualityCategory.IDENTITY, "identity", "full_name", "O nome completo é obrigatório.", "Informe o nome completo no currículo."))

    def _validate_contact(self, snapshot: StructuredResumeSnapshot, issues: list[StructuredResumeQualityIssue]) -> None:
        email = snapshot.contact.email
        if email is not None and not _valid_email(email):
            issues.append(_issue("CONTACT_EMAIL_INVALID", StructuredResumeQualitySeverity.WARNING, StructuredResumeQualityCategory.CONTACT, "contact", "email", "O e-mail informado possui formato inválido.", "Informe um e-mail com usuário e domínio válidos."))

    def _validate_skills(self, snapshot: StructuredResumeSnapshot, issues: list[StructuredResumeQualityIssue]) -> None:
        seen: set[str] = set()
        for index, skill in enumerate(snapshot.skills):
            normalized = _normalize(skill)
            if not normalized:
                issues.append(_issue("SKILL_EMPTY", StructuredResumeQualitySeverity.WARNING, StructuredResumeQualityCategory.SKILLS, "skills", str(index), "Existe uma competência vazia.", "Remova a competência vazia ou informe seu nome."))
            elif normalized in seen:
                issues.append(_issue("SKILL_DUPLICATE", StructuredResumeQualitySeverity.INFO, StructuredResumeQualityCategory.DUPLICATION, "skills", str(index), "Existe uma competência duplicada.", "Mantenha apenas uma ocorrência da competência."))
            else:
                seen.add(normalized)

    def _validate_experiences(self, snapshot: StructuredResumeSnapshot, issues: list[StructuredResumeQualityIssue]) -> None:
        seen: set[tuple[str, str, str, str]] = set()
        previous_start: date | None = None
        for index, experience in enumerate(snapshot.experiences):
            section = f"experiences[{index}]"
            if _empty(experience.company):
                issues.append(_issue("EXPERIENCE_COMPANY_REQUIRED", StructuredResumeQualitySeverity.WARNING, StructuredResumeQualityCategory.EXPERIENCE, section, "company", "A experiência não possui empresa informada.", "Informe a empresa ou organização da experiência."))
            if _empty(experience.role):
                issues.append(_issue("EXPERIENCE_ROLE_REQUIRED", StructuredResumeQualitySeverity.WARNING, StructuredResumeQualityCategory.EXPERIENCE, section, "role", "A experiência não possui cargo informado.", "Informe o cargo ou função exercida."))
            start, end = _parse_date(experience.start_date), _parse_date(experience.end_date)
            if start is not None and end is not None and start > end:
                issues.append(_issue("EXPERIENCE_PERIOD_INVALID", StructuredResumeQualitySeverity.WARNING, StructuredResumeQualityCategory.CONSISTENCY, section, "period", "O período da experiência está invertido.", "Informe uma data inicial anterior ou igual à data final."))
            key = (_normalize(experience.company), _normalize(experience.role), _normalize(experience.start_date), _normalize(experience.end_date))
            if key in seen and any(key):
                issues.append(_issue("EXPERIENCE_DUPLICATE", StructuredResumeQualitySeverity.WARNING, StructuredResumeQualityCategory.DUPLICATION, section, "experience", "Existe uma experiência duplicada.", "Mantenha apenas uma ocorrência da experiência."))
            seen.add(key)
            if start is not None and previous_start is not None and start > previous_start:
                issues.append(_issue("CHRONOLOGY_ORDER_WARNING", StructuredResumeQualitySeverity.WARNING, StructuredResumeQualityCategory.CHRONOLOGY, section, "start_date", "As experiências não estão em ordem cronológica decrescente.", "Ordene as experiências da mais recente para a mais antiga."))
            if start is not None:
                previous_start = start

    def _validate_duplicates(self, snapshot: StructuredResumeSnapshot, issues: list[StructuredResumeQualityIssue]) -> None:
        self._duplicate_issue(snapshot.education, lambda item: (_normalize(item.degree), _normalize(item.institution), _normalize(item.start_date), _normalize(item.end_date)), "EDUCATION_DUPLICATE", StructuredResumeQualityCategory.DUPLICATION, "education", "education", "Existe uma formação duplicada.", "Mantenha apenas uma ocorrência da formação.", issues)
        self._duplicate_issue(snapshot.certifications, lambda item: (_normalize(item.name), _normalize(item.issuer), _normalize(item.issued_date)), "CERTIFICATION_DUPLICATE", StructuredResumeQualityCategory.DUPLICATION, "certifications", "certification", "Existe uma certificação duplicada.", "Mantenha apenas uma ocorrência da certificação.", issues)
        seen: dict[str, str] = {}
        for index, language in enumerate(snapshot.languages):
            name = _normalize(language.name)
            if name in seen and name:
                category = StructuredResumeQualityCategory.CONSISTENCY if seen[name] != _normalize(language.proficiency) else StructuredResumeQualityCategory.DUPLICATION
                code = "LANGUAGE_CONFLICTING_PROFICIENCY" if category is StructuredResumeQualityCategory.CONSISTENCY else "LANGUAGE_DUPLICATE"
                message = "O idioma possui níveis de proficiência conflitantes." if code == "LANGUAGE_CONFLICTING_PROFICIENCY" else "Existe um idioma duplicado."
                recommendation = "Revise e mantenha um único nível de proficiência para o idioma." if code == "LANGUAGE_CONFLICTING_PROFICIENCY" else "Mantenha apenas uma ocorrência do idioma."
                issues.append(_issue(code, StructuredResumeQualitySeverity.WARNING, category, f"languages[{index}]", "name", message, recommendation))
            elif name:
                seen[name] = _normalize(language.proficiency)

    @staticmethod
    def _duplicate_issue(items: Iterable[object], key_builder: object, code: str, category: StructuredResumeQualityCategory, section_name: str, field_name: str, message: str, recommendation: str, issues: list[StructuredResumeQualityIssue]) -> None:
        seen: set[tuple[str, ...]] = set()
        for index, item in enumerate(items):
            key = key_builder(item)  # type: ignore[operator]
            if key in seen and any(key):
                issues.append(_issue(code, StructuredResumeQualitySeverity.WARNING, category, f"{section_name}[{index}]", field_name, message, recommendation))
            seen.add(key)

    def _validate_content(self, snapshot: StructuredResumeSnapshot, issues: list[StructuredResumeQualityIssue]) -> None:
        for section, field_name, value in _snapshot_text_values(snapshot):
            normalized = _normalize(value)
            if normalized in self._PLACEHOLDERS:
                issues.append(_issue("CONTENT_PLACEHOLDER_DETECTED", StructuredResumeQualitySeverity.WARNING, StructuredResumeQualityCategory.STRUCTURE, section, field_name, "Foi detectado um placeholder no currículo.", "Substitua o placeholder por conteúdo profissional."))
            if _contains_forbidden_control(value):
                issues.append(_issue("CONTENT_CONTROL_CHARACTER", StructuredResumeQualitySeverity.ERROR, StructuredResumeQualityCategory.EXPORTABILITY, section, field_name, "Foi detectado um caractere de controle incompatível com exportação confiável.", "Remova o caractere de controle do conteúdo."))
            if _contains_technical_artifact(value):
                issues.append(_issue("CONTENT_TECHNICAL_ARTIFACT", StructuredResumeQualitySeverity.WARNING, StructuredResumeQualityCategory.STRUCTURE, section, field_name, "Foi detectado conteúdo técnico exposto no currículo.", "Remova artefatos técnicos, caminhos locais ou informações de depuração."))

    @staticmethod
    def _validate_exportability(snapshot: StructuredResumeSnapshot, issues: list[StructuredResumeQualityIssue]) -> None:
        has_professional_content = bool(snapshot.summary and snapshot.summary.strip()) or bool(snapshot.skills) or bool(snapshot.experiences) or bool(snapshot.education) or bool(snapshot.certifications) or bool(snapshot.projects)
        if _empty(snapshot.identity.full_name) or not has_professional_content:
            issues.append(_issue("EXPORT_MINIMUM_CONTENT_REQUIRED", StructuredResumeQualitySeverity.ERROR, StructuredResumeQualityCategory.EXPORTABILITY, "snapshot", "content", "O currículo não possui conteúdo mínimo para exportação útil.", "Informe nome e ao menos uma seção profissional relevante."))


class ValidateEffectiveStructuredResumeQualityUseCase:
    """Validate only the persisted effective snapshot selected by an application."""

    def __init__(self, effective_resume_use_case: EffectiveApplicationResumeUseCase, validator: StructuredResumeQualityValidator) -> None:
        self._effective_resume_use_case = effective_resume_use_case
        self._validator = validator

    def execute(self, request: ValidateEffectiveStructuredResumeQualityRequest) -> ValidateEffectiveStructuredResumeQualityResult:
        """Resolve once, validate once, and return no persistence side effects."""
        effective = self._effective_resume_use_case.execute(EffectiveApplicationResumeRequest(request.application_id))
        mapped = self._effective_status(effective.status)
        if mapped is not None:
            return self._result(mapped, request.application_id, effective.resume_source, effective.curriculum_id, effective.effective_resume_version_id, message=effective.message)
        if effective.structured_content_status is StructuredResumeContentStatus.UNSUPPORTED_SCHEMA:
            return self._result(EffectiveStructuredResumeQualityStatus.UNSUPPORTED_SCHEMA, request.application_id, effective.resume_source, effective.curriculum_id, effective.effective_resume_version_id, message="O currículo utiliza uma estrutura ainda não suportada para validação.")
        if effective.structured_resume is None:
            return self._result(EffectiveStructuredResumeQualityStatus.STRUCTURED_CONTENT_REQUIRED, request.application_id, effective.resume_source, effective.curriculum_id, effective.effective_resume_version_id, message="O currículo efetivo não possui conteúdo estruturado disponível para validação.")
        try:
            validation = self._validator.validate(effective.structured_resume)
        except (TypeError, ValueError):
            return self._result(EffectiveStructuredResumeQualityStatus.VALIDATION_FAILED, request.application_id, effective.resume_source, effective.curriculum_id, effective.effective_resume_version_id, message="Não foi possível validar a qualidade do currículo.")
        message = "Validação concluída. O currículo não possui problemas estruturais críticos." if validation.is_valid else "Validação concluída. Foram encontrados problemas estruturais que precisam de revisão."
        return ValidateEffectiveStructuredResumeQualityResult(EffectiveStructuredResumeQualityStatus.SUCCESS, request.application_id, effective.resume_source, effective.curriculum_id, effective.effective_resume_version_id, validation.is_valid, validation.score, validation.issues, validation.error_count, validation.warning_count, validation.info_count, _summary(validation), message)

    @staticmethod
    def _effective_status(status: EffectiveApplicationResumeStatus) -> EffectiveStructuredResumeQualityStatus | None:
        mapping = {
            EffectiveApplicationResumeStatus.APPLICATION_NOT_FOUND: EffectiveStructuredResumeQualityStatus.APPLICATION_NOT_FOUND,
            EffectiveApplicationResumeStatus.CURRICULUM_NOT_FOUND: EffectiveStructuredResumeQualityStatus.CURRICULUM_NOT_FOUND,
            EffectiveApplicationResumeStatus.SELECTED_VERSION_NOT_FOUND: EffectiveStructuredResumeQualityStatus.ADOPTED_RESUME_VERSION_NOT_FOUND,
            EffectiveApplicationResumeStatus.SELECTED_VERSION_CURRICULUM_MISMATCH: EffectiveStructuredResumeQualityStatus.ADOPTED_RESUME_VERSION_NOT_FOUND,
            EffectiveApplicationResumeStatus.SELECTION_INCONSISTENT: EffectiveStructuredResumeQualityStatus.ADOPTED_RESUME_VERSION_NOT_FOUND,
            EffectiveApplicationResumeStatus.CURRICULUM_REQUIRED: EffectiveStructuredResumeQualityStatus.STRUCTURED_CONTENT_REQUIRED,
            EffectiveApplicationResumeStatus.CONTENT_UNAVAILABLE: EffectiveStructuredResumeQualityStatus.STRUCTURED_CONTENT_REQUIRED,
        }
        return mapping.get(status)

    @staticmethod
    def _result(status: EffectiveStructuredResumeQualityStatus, application_id: int, source: ApplicationResumeSource, curriculum_id: int | None, resume_version_id: int | None, *, message: str) -> ValidateEffectiveStructuredResumeQualityResult:
        return ValidateEffectiveStructuredResumeQualityResult(status, application_id, source, curriculum_id, resume_version_id, message=message)


def _issue(code: str, severity: StructuredResumeQualitySeverity, category: StructuredResumeQualityCategory, section: str, field_name: str, message: str, recommendation: str) -> StructuredResumeQualityIssue:
    return StructuredResumeQualityIssue(code, severity, category, section, field_name, message, recommendation)


def _issue_sort_key(issue: StructuredResumeQualityIssue) -> tuple[int, str, str, str, str]:
    order = {StructuredResumeQualitySeverity.ERROR: 0, StructuredResumeQualitySeverity.WARNING: 1, StructuredResumeQualitySeverity.INFO: 2}
    return order[issue.severity], issue.category.value, issue.section, issue.field, issue.code


def _summary(validation: StructuredResumeQualityValidation) -> str:
    if not validation.issues:
        return "Nenhum problema estrutural identificado."
    parts = (
        _count_label(validation.error_count, "erro"),
        _count_label(validation.warning_count, "alerta"),
        _count_label(validation.info_count, "observação"),
    )
    return ", ".join(part for part in parts if part) + "."


def _count_label(count: int, singular: str) -> str:
    if count == 0:
        return ""
    suffix = "" if count == 1 else "s"
    return f"{count} {singular}{suffix}"


def _empty(value: str | None) -> bool:
    return not value or not value.strip()


def _normalize(value: str | None) -> str:
    return " ".join((value or "").split()).casefold()


def _valid_email(value: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value))


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    for pattern in ("%Y-%m-%d", "%Y-%m"):
        try:
            return date.fromisoformat(value) if pattern == "%Y-%m-%d" else date.fromisoformat(f"{value}-01")
        except ValueError:
            continue
    return None


def _contains_forbidden_control(value: str | None) -> bool:
    return any(ord(character) < 32 and character not in "\t\n\r" for character in value or "")


def _contains_technical_artifact(value: str | None) -> bool:
    candidate = value or ""
    return bool(re.search(r"Traceback \(most recent call last\)|[A-Za-z]:\\\\|\{\s*\"[^\"]+\"\s*:|(?:api[_-]?key|sk-[A-Za-z0-9_-]{12,})|(?:debug|prompt)\s*:", candidate, re.IGNORECASE))


def _snapshot_text_values(snapshot: StructuredResumeSnapshot) -> Iterable[tuple[str, str, str | None]]:
    yield "identity", "full_name", snapshot.identity.full_name
    yield "identity", "professional_title", snapshot.identity.professional_title
    yield "summary", "content", snapshot.summary
    yield "contact", "email", snapshot.contact.email
    for index, skill in enumerate(snapshot.skills):
        yield f"skills[{index}]", "value", skill
    for index, experience in enumerate(snapshot.experiences):
        yield f"experiences[{index}]", "company", experience.company
        yield f"experiences[{index}]", "role", experience.role
        yield f"experiences[{index}]", "summary", experience.summary
        for achievement_index, achievement in enumerate(experience.achievements):
            yield f"experiences[{index}]", f"achievements[{achievement_index}]", achievement
    for index, education in enumerate(snapshot.education):
        yield f"education[{index}]", "institution", education.institution
        yield f"education[{index}]", "degree", education.degree
    for index, certification in enumerate(snapshot.certifications):
        yield f"certifications[{index}]", "name", certification.name
        yield f"certifications[{index}]", "issuer", certification.issuer
    for index, language in enumerate(snapshot.languages):
        yield f"languages[{index}]", "name", language.name
