"""Immutable, versioned structured resume snapshots and their JSON codec."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from enum import StrEnum
import json


class StructuredResumeContentStatus(StrEnum):
    """Availability of the optional structured representation."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    INVALID = "invalid"
    UNSUPPORTED_SCHEMA = "unsupported_schema"


class StructuredResumeValidationError(ValueError):
    """Raised when a snapshot does not comply with the supported schema."""


class UnsupportedStructuredResumeSchemaError(StructuredResumeValidationError):
    """Raised when a payload declares a schema version not supported here."""


@dataclass(frozen=True)
class StructuredResumeIdentity:
    full_name: str | None = None
    professional_title: str | None = None
    location: str | None = None


@dataclass(frozen=True)
class StructuredResumeContact:
    email: str | None = None
    phone: str | None = None
    linkedin: str | None = None
    portfolio: str | None = None
    website: str | None = None


@dataclass(frozen=True)
class StructuredResumeExperience:
    company: str | None = None
    role: str | None = None
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool = False
    summary: str | None = None
    achievements: tuple[str, ...] = ()


@dataclass(frozen=True)
class StructuredResumeEducation:
    institution: str | None = None
    degree: str | None = None
    field: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    status: str | None = None
    details: str | None = None


@dataclass(frozen=True)
class StructuredResumeCertification:
    name: str | None = None
    issuer: str | None = None
    issued_date: str | None = None
    credential_id: str | None = None
    url: str | None = None


@dataclass(frozen=True)
class StructuredResumeCourse:
    name: str | None = None
    provider: str | None = None
    completed_date: str | None = None
    details: str | None = None


@dataclass(frozen=True)
class StructuredResumeLanguage:
    name: str | None = None
    proficiency: str | None = None


@dataclass(frozen=True)
class StructuredResumeProject:
    name: str | None = None
    description: str | None = None
    url: str | None = None
    highlights: tuple[str, ...] = ()


@dataclass(frozen=True)
class StructuredResumeAdditionalSection:
    title: str | None = None
    paragraphs: tuple[str, ...] = ()
    items: tuple[str, ...] = ()
    order: int = 0


@dataclass(frozen=True)
class StructuredResumeSnapshot:
    """The immutable schema-v1 aggregate persisted with a resume source."""

    schema_version: int
    identity: StructuredResumeIdentity = field(default_factory=StructuredResumeIdentity)
    contact: StructuredResumeContact = field(default_factory=StructuredResumeContact)
    summary: str | None = None
    skills: tuple[str, ...] = ()
    experiences: tuple[StructuredResumeExperience, ...] = ()
    education: tuple[StructuredResumeEducation, ...] = ()
    certifications: tuple[StructuredResumeCertification, ...] = ()
    courses: tuple[StructuredResumeCourse, ...] = ()
    languages: tuple[StructuredResumeLanguage, ...] = ()
    projects: tuple[StructuredResumeProject, ...] = ()
    additional_sections: tuple[StructuredResumeAdditionalSection, ...] = ()


class StructuredResumeSnapshotCodec:
    """Validate and deterministically convert schema-v1 resume snapshots."""

    _VERSION = 1
    _TOP_LEVEL_FIELDS = frozenset(StructuredResumeSnapshot.__dataclass_fields__)

    def loads(self, value: str) -> StructuredResumeSnapshot:
        """Deserialize a JSON string without silently accepting malformed data."""
        try:
            payload = json.loads(value)
        except (TypeError, json.JSONDecodeError) as error:
            raise StructuredResumeValidationError("Structured resume JSON is malformed.") from error
        return self.from_payload(payload)

    def from_payload(self, payload: object) -> StructuredResumeSnapshot:
        """Validate a mapping and return its immutable representation."""
        root = self._mapping(payload, "snapshot")
        if "schema_version" not in root:
            raise StructuredResumeValidationError("snapshot.schema_version is required.")
        schema_version = self._integer(root["schema_version"], "schema_version")
        if schema_version != self._VERSION:
            raise UnsupportedStructuredResumeSchemaError(
                f"Unsupported structured resume schema version: {schema_version}."
            )
        self._require_exact_fields(root, self._TOP_LEVEL_FIELDS, "snapshot")
        return StructuredResumeSnapshot(
            schema_version=schema_version,
            identity=self._identity(root["identity"]),
            contact=self._contact(root["contact"]),
            summary=self._optional_string(root["summary"], "summary"),
            skills=self._string_tuple(root["skills"], "skills"),
            experiences=tuple(
                self._experience(item, f"experiences[{index}]")
                for index, item in enumerate(self._array(root["experiences"], "experiences"))
            ),
            education=tuple(
                self._education(item, f"education[{index}]")
                for index, item in enumerate(self._array(root["education"], "education"))
            ),
            certifications=tuple(
                self._certification(item, f"certifications[{index}]")
                for index, item in enumerate(self._array(root["certifications"], "certifications"))
            ),
            courses=tuple(
                self._course(item, f"courses[{index}]")
                for index, item in enumerate(self._array(root["courses"], "courses"))
            ),
            languages=tuple(
                self._language(item, f"languages[{index}]")
                for index, item in enumerate(self._array(root["languages"], "languages"))
            ),
            projects=tuple(
                self._project(item, f"projects[{index}]")
                for index, item in enumerate(self._array(root["projects"], "projects"))
            ),
            additional_sections=tuple(
                self._additional_section(item, f"additional_sections[{index}]")
                for index, item in enumerate(
                    self._array(root["additional_sections"], "additional_sections")
                )
            ),
        )

    def dumps(self, snapshot: StructuredResumeSnapshot) -> str:
        """Serialize a supported snapshot with deterministic UTF-8-safe JSON."""
        if not isinstance(snapshot, StructuredResumeSnapshot):
            raise StructuredResumeValidationError("A StructuredResumeSnapshot is required.")
        validated = self.loads(json.dumps(asdict(snapshot)))
        return json.dumps(asdict(validated), ensure_ascii=False, separators=(",", ":"))

    def decode(
        self, value: str | None
    ) -> tuple[StructuredResumeSnapshot | None, StructuredResumeContentStatus]:
        """Decode database content into an explicit non-throwing read status."""
        if value is None:
            return None, StructuredResumeContentStatus.UNAVAILABLE
        try:
            return self.loads(value), StructuredResumeContentStatus.AVAILABLE
        except UnsupportedStructuredResumeSchemaError:
            return None, StructuredResumeContentStatus.UNSUPPORTED_SCHEMA
        except StructuredResumeValidationError:
            return None, StructuredResumeContentStatus.INVALID

    @staticmethod
    def _mapping(value: object, label: str) -> Mapping[str, object]:
        if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
            raise StructuredResumeValidationError(f"{label} must be an object.")
        return value

    @staticmethod
    def _array(value: object, label: str) -> list[object]:
        if not isinstance(value, list):
            raise StructuredResumeValidationError(f"{label} must be an array.")
        return value

    @staticmethod
    def _integer(value: object, label: str) -> int:
        if not isinstance(value, int) or isinstance(value, bool):
            raise StructuredResumeValidationError(f"{label} must be an integer.")
        return value

    @staticmethod
    def _optional_string(value: object, label: str) -> str | None:
        if value is None or isinstance(value, str):
            return value
        raise StructuredResumeValidationError(f"{label} must be a string or null.")

    def _string_tuple(self, value: object, label: str) -> tuple[str, ...]:
        return tuple(
            self._required_string(item, f"{label}[{index}]")
            for index, item in enumerate(self._array(value, label))
        )

    def _object(self, value: object, fields: tuple[str, ...], label: str) -> Mapping[str, object]:
        result = self._mapping(value, label)
        self._require_exact_fields(result, frozenset(fields), label)
        return result

    @staticmethod
    def _require_exact_fields(
        value: Mapping[str, object], expected: frozenset[str], label: str
    ) -> None:
        actual = set(value)
        missing = expected - actual
        unknown = actual - expected
        if missing or unknown:
            raise StructuredResumeValidationError(
                f"{label} fields are invalid; missing={sorted(missing)}, unknown={sorted(unknown)}."
            )

    def _identity(self, value: object) -> StructuredResumeIdentity:
        item = self._object(value, ("full_name", "professional_title", "location"), "identity")
        return StructuredResumeIdentity(**{key: self._optional_string(item[key], key) for key in item})

    def _contact(self, value: object) -> StructuredResumeContact:
        fields = ("email", "phone", "linkedin", "portfolio", "website")
        item = self._object(value, fields, "contact")
        return StructuredResumeContact(**{key: self._optional_string(item[key], key) for key in item})

    def _experience(self, value: object, label: str) -> StructuredResumeExperience:
        fields = ("company", "role", "location", "start_date", "end_date", "is_current", "summary", "achievements")
        item = self._object(value, fields, label)
        is_current = item["is_current"]
        if not isinstance(is_current, bool):
            raise StructuredResumeValidationError(f"{label}.is_current must be a boolean.")
        return StructuredResumeExperience(
            **{key: self._optional_string(item[key], f"{label}.{key}") for key in fields if key not in {"is_current", "achievements"}},
            is_current=is_current,
            achievements=self._string_tuple(item["achievements"], f"{label}.achievements"),
        )

    def _education(self, value: object, label: str) -> StructuredResumeEducation:
        fields = ("institution", "degree", "field", "start_date", "end_date", "status", "details")
        item = self._object(value, fields, label)
        return StructuredResumeEducation(**{key: self._optional_string(item[key], f"{label}.{key}") for key in fields})

    def _certification(self, value: object, label: str) -> StructuredResumeCertification:
        fields = ("name", "issuer", "issued_date", "credential_id", "url")
        item = self._object(value, fields, label)
        return StructuredResumeCertification(**{key: self._optional_string(item[key], f"{label}.{key}") for key in fields})

    def _course(self, value: object, label: str) -> StructuredResumeCourse:
        fields = ("name", "provider", "completed_date", "details")
        item = self._object(value, fields, label)
        return StructuredResumeCourse(**{key: self._optional_string(item[key], f"{label}.{key}") for key in fields})

    def _language(self, value: object, label: str) -> StructuredResumeLanguage:
        fields = ("name", "proficiency")
        item = self._object(value, fields, label)
        return StructuredResumeLanguage(**{key: self._optional_string(item[key], f"{label}.{key}") for key in fields})

    def _project(self, value: object, label: str) -> StructuredResumeProject:
        fields = ("name", "description", "url", "highlights")
        item = self._object(value, fields, label)
        return StructuredResumeProject(
            name=self._optional_string(item["name"], f"{label}.name"),
            description=self._optional_string(item["description"], f"{label}.description"),
            url=self._optional_string(item["url"], f"{label}.url"),
            highlights=self._string_tuple(item["highlights"], f"{label}.highlights"),
        )

    def _additional_section(self, value: object, label: str) -> StructuredResumeAdditionalSection:
        fields = ("title", "paragraphs", "items", "order")
        item = self._object(value, fields, label)
        return StructuredResumeAdditionalSection(
            title=self._optional_string(item["title"], f"{label}.title"),
            paragraphs=self._string_tuple(item["paragraphs"], f"{label}.paragraphs"),
            items=self._string_tuple(item["items"], f"{label}.items"),
            order=self._integer(item["order"], f"{label}.order"),
        )

    @staticmethod
    def _required_string(value: object, label: str) -> str:
        if isinstance(value, str):
            return value
        raise StructuredResumeValidationError(f"{label} must be a string.")
