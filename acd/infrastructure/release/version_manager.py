"""Version manager with semantic versioning support."""

import re
from typing import Tuple
from datetime import datetime


class SemanticVersion:
    """Semantic version (SemVer) parser and comparator."""

    SEMVER_REGEX = r"^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.-]+))?(?:\+([a-zA-Z0-9.-]+))?$"

    def __init__(self, version_string: str):
        """Initialize semantic version.
        
        Args:
            version_string: Version string (e.g., "0.4.0", "1.0.0-beta.1", "2.0.0+build.123")
        """
        match = re.match(self.SEMVER_REGEX, version_string)
        if not match:
            raise ValueError(f"Invalid semantic version format: {version_string}")

        self.major: int = int(match.group(1))
        self.minor: int = int(match.group(2))
        self.patch: int = int(match.group(3))
        self.prerelease: str | None = match.group(4)
        self.build: str | None = match.group(5)
        self.original: str = version_string

    def __str__(self) -> str:
        """Return version string."""
        return self.original

    def __repr__(self) -> str:
        """Return detailed representation."""
        return f"SemanticVersion({self.original})"

    def __eq__(self, other: "SemanticVersion") -> bool:
        """Check equality (ignoring build metadata)."""
        if not isinstance(other, SemanticVersion):
            return False
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
            and self.prerelease == other.prerelease
        )

    def __lt__(self, other: "SemanticVersion") -> bool:
        """Check if less than (comparison)."""
        if not isinstance(other, SemanticVersion):
            raise TypeError(f"Cannot compare SemanticVersion with {type(other)}")

        # Compare major.minor.patch
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        if self.patch != other.patch:
            return self.patch < other.patch

        # Prerelease versions are less than release versions
        if self.prerelease and not other.prerelease:
            return True
        if not self.prerelease and other.prerelease:
            return False

        # Both have prerelease or both don't
        if self.prerelease and other.prerelease:
            return self.prerelease < other.prerelease

        return False

    def __le__(self, other: "SemanticVersion") -> bool:
        """Check if less than or equal."""
        return self == other or self < other

    def __gt__(self, other: "SemanticVersion") -> bool:
        """Check if greater than."""
        return not (self <= other)

    def __ge__(self, other: "SemanticVersion") -> bool:
        """Check if greater than or equal."""
        return not (self < other)

    def __hash__(self) -> int:
        """Make hashable for use in sets/dicts."""
        return hash((self.major, self.minor, self.patch, self.prerelease))

    def is_major_release(self) -> bool:
        """Check if this is a major version release."""
        return self.minor == 0 and self.patch == 0

    def is_minor_release(self) -> bool:
        """Check if this is a minor version release."""
        return self.patch == 0 and not self.is_major_release()

    def is_patch_release(self) -> bool:
        """Check if this is a patch version release."""
        return self.patch > 0

    def is_prerelease(self) -> bool:
        """Check if this is a prerelease version."""
        return self.prerelease is not None

    def is_beta(self) -> bool:
        """Check if this is a beta version."""
        return self.prerelease is not None and "beta" in self.prerelease.lower()

    def is_alpha(self) -> bool:
        """Check if this is an alpha version."""
        return self.prerelease is not None and "alpha" in self.prerelease.lower()

    def is_rc(self) -> bool:
        """Check if this is a release candidate."""
        return self.prerelease is not None and "rc" in self.prerelease.lower()

    def get_next_major(self) -> "SemanticVersion":
        """Get next major version."""
        return SemanticVersion(f"{self.major + 1}.0.0")

    def get_next_minor(self) -> "SemanticVersion":
        """Get next minor version."""
        return SemanticVersion(f"{self.major}.{self.minor + 1}.0")

    def get_next_patch(self) -> "SemanticVersion":
        """Get next patch version."""
        return SemanticVersion(f"{self.major}.{self.minor}.{self.patch + 1}")

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "version": str(self),
            "major": self.major,
            "minor": self.minor,
            "patch": self.patch,
            "prerelease": self.prerelease,
            "is_prerelease": self.is_prerelease(),
            "is_beta": self.is_beta(),
            "is_rc": self.is_rc(),
        }


class VersionManager:
    """Manage versions and compatibility checks."""

    @staticmethod
    def parse_version(version_string: str) -> SemanticVersion:
        """Parse version string to SemanticVersion."""
        return SemanticVersion(version_string)

    @staticmethod
    def compare_versions(version1: str, version2: str) -> int:
        """Compare two versions.
        
        Returns:
            -1 if version1 < version2
            0 if version1 == version2
            1 if version1 > version2
        """
        v1 = SemanticVersion(version1)
        v2 = SemanticVersion(version2)

        if v1 < v2:
            return -1
        elif v1 > v2:
            return 1
        else:
            return 0

    @staticmethod
    def is_compatible(current_version: str, min_required: str, max_allowed: str | None = None) -> bool:
        """Check if current version is within compatibility range.
        
        Args:
            current_version: Current version
            min_required: Minimum required version
            max_allowed: Maximum allowed version (optional)
        """
        current = SemanticVersion(current_version)
        min_req = SemanticVersion(min_required)

        if current < min_req:
            return False

        if max_allowed:
            max_ver = SemanticVersion(max_allowed)
            if current > max_ver:
                return False

        return True

    @staticmethod
    def get_upgrade_path(from_version: str, to_version: str, available_versions: list[str]) -> list[str]:
        """Get upgrade path from one version to another.
        
        Returns:
            List of versions to upgrade through (in order)
        """
        from_v = SemanticVersion(from_version)
        to_v = SemanticVersion(to_version)

        if from_v > to_v:
            raise ValueError(f"Cannot upgrade from {from_version} to {to_version}")

        if from_v == to_v:
            return [from_version]

        # Parse and sort available versions
        versions = [SemanticVersion(v) for v in available_versions]
        versions.sort()

        # Find versions in range
        path = [str(from_v)]
        for v in versions:
            if v > from_v and v <= to_v:
                path.append(str(v))

        return path

    @staticmethod
    def format_version_info(version_string: str) -> str:
        """Format version string for display."""
        v = SemanticVersion(version_string)
        info = f"v{v.major}.{v.minor}.{v.patch}"

        if v.is_beta():
            info += " (Beta)"
        elif v.is_alpha():
            info += " (Alpha)"
        elif v.is_rc():
            info += " (RC)"

        return info
