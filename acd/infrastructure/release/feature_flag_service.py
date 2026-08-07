"""Feature flag service for feature toggling."""

from datetime import datetime
import random

from acd.version import get_version


class FeatureFlagService:
    """Service for managing feature flags."""

    def __init__(self, session=None):
        """Initialize feature flag service.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self._cache: dict[str, dict] = {}
        self._cache_timestamp: dict[str, datetime] = {}
        self.cache_ttl_minutes = 60  # Cache for 60 minutes

    def is_enabled(
        self,
        feature_name: str,
        current_version: str = get_version(),
        user_id: str | None = None,
    ) -> bool:
        """Check if a feature is enabled.

        Args:
            feature_name: Name of the feature
            current_version: Current application version
            user_id: Optional user ID for user-specific rollouts

        Returns:
            True if feature is enabled
        """
        from acd.domain.release import FeatureFlag

        # Check cache first
        if self._is_cache_valid(feature_name):
            return self._check_cached_flag(feature_name, current_version, user_id)

        # Load from database
        if not self.session:
            return False

        try:
            flag = self.session.query(FeatureFlag).filter_by(feature_name=feature_name).first()

            if not flag:
                return False

            # Cache the flag
            self._cache[feature_name] = {
                "is_enabled": flag.is_enabled,
                "is_beta": flag.is_beta,
                "rollout_percentage": flag.rollout_percentage,
                "target_versions": flag.target_versions,
                "experimental": flag.experimental,
            }
            self._cache_timestamp[feature_name] = datetime.now()

            return self._check_flag(flag, current_version, user_id)

        except Exception:
            return False

    def _is_cache_valid(self, feature_name: str) -> bool:
        """Check if cache entry is still valid."""
        if feature_name not in self._cache_timestamp:
            return False

        now = datetime.now()
        cached_at = self._cache_timestamp[feature_name]
        elapsed_minutes = (now - cached_at).total_seconds() / 60

        return elapsed_minutes < self.cache_ttl_minutes

    def _check_cached_flag(
        self,
        feature_name: str,
        current_version: str,
        user_id: str | None,
    ) -> bool:
        """Check flag using cached data."""
        cached = self._cache.get(feature_name, {})

        if not cached.get("is_enabled"):
            return False

        target_versions = cached.get("target_versions", [])
        if target_versions and current_version not in target_versions:
            return False

        rollout_percentage = cached.get("rollout_percentage", 100)
        if rollout_percentage < 100:
            return self._check_rollout(user_id, rollout_percentage)

        return True

    def _check_flag(self, flag, current_version: str, user_id: str | None) -> bool:
        """Check flag status."""
        if not flag.is_enabled:
            return False

        if flag.target_versions and current_version not in flag.target_versions:
            return False

        if flag.rollout_percentage < 100:
            return self._check_rollout(user_id, flag.rollout_percentage)

        return True

    def _check_rollout(self, user_id: str | None, rollout_percentage: int) -> bool:
        """Check if user is in rollout percentage.

        Uses consistent hashing based on user_id if provided.
        """
        if rollout_percentage >= 100:
            return True

        if rollout_percentage <= 0:
            return False

        if user_id:
            # Use hash of user_id for consistent rollout
            hash_val = hash(user_id) % 100
            return hash_val < rollout_percentage
        else:
            # Random rollout if no user_id
            return random.randint(0, 99) < rollout_percentage

    def enable_feature(self, feature_name: str) -> bool:
        """Enable a feature."""
        from acd.domain.release import FeatureFlag

        if not self.session:
            return False

        try:
            flag = self.session.query(FeatureFlag).filter_by(feature_name=feature_name).first()

            if not flag:
                # Create new flag
                flag = FeatureFlag(
                    feature_name=feature_name,
                    is_enabled=True,
                    rollout_percentage=100,
                )
                self.session.add(flag)
            else:
                flag.is_enabled = True
                flag.rollout_percentage = 100

            self.session.commit()
            self._invalidate_cache(feature_name)
            return True

        except Exception:
            self.session.rollback()
            return False

    def disable_feature(self, feature_name: str) -> bool:
        """Disable a feature."""
        from acd.domain.release import FeatureFlag

        if not self.session:
            return False

        try:
            flag = self.session.query(FeatureFlag).filter_by(feature_name=feature_name).first()

            if not flag:
                return False

            flag.is_enabled = False
            self.session.commit()
            self._invalidate_cache(feature_name)
            return True

        except Exception:
            self.session.rollback()
            return False

    def set_rollout_percentage(self, feature_name: str, percentage: int) -> bool:
        """Set rollout percentage for gradual rollout.

        Args:
            feature_name: Feature name
            percentage: Percentage 0-100

        Returns:
            True if successful
        """
        from acd.domain.release import FeatureFlag

        if not 0 <= percentage <= 100:
            return False

        if not self.session:
            return False

        try:
            flag = self.session.query(FeatureFlag).filter_by(feature_name=feature_name).first()

            if not flag:
                flag = FeatureFlag(
                    feature_name=feature_name,
                    is_enabled=True,
                    rollout_percentage=percentage,
                )
                self.session.add(flag)
            else:
                flag.rollout_percentage = percentage

            self.session.commit()
            self._invalidate_cache(feature_name)
            return True

        except Exception:
            self.session.rollback()
            return False

    def get_all_flags(self, current_version: str = get_version()) -> list[dict]:
        """Get all feature flags for current version."""
        from acd.domain.release import FeatureFlag

        if not self.session:
            return []

        try:
            flags = self.session.query(FeatureFlag).all()
            result = []

            for flag in flags:
                if flag.is_enabled_for_version(current_version):
                    result.append(flag.to_dict())

            return result

        except Exception:
            return []

    def _invalidate_cache(self, feature_name: str) -> None:
        """Invalidate cache for a feature."""
        self._cache.pop(feature_name, None)
        self._cache_timestamp.pop(feature_name, None)

    def clear_cache(self) -> None:
        """Clear all cache."""
        self._cache.clear()
        self._cache_timestamp.clear()


# Global feature flag service instance
_feature_flag_service: FeatureFlagService | None = None


def get_feature_flag_service() -> FeatureFlagService:
    """Get singleton feature flag service."""
    global _feature_flag_service
    if _feature_flag_service is None:
        _feature_flag_service = FeatureFlagService()
    return _feature_flag_service


def initialize_feature_flag_service(session=None) -> FeatureFlagService:
    """Initialize global feature flag service."""
    global _feature_flag_service
    _feature_flag_service = FeatureFlagService(session)
    return _feature_flag_service
