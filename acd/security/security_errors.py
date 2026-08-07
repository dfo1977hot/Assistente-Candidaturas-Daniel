"""Safe typed failures raised at security boundaries."""


class SecurityBoundaryError(ValueError):
    """Base error whose message is safe for an application boundary."""


class SecretConfigurationError(SecurityBoundaryError):
    """A required secret is absent or invalid."""


class PathRejectedError(SecurityBoundaryError):
    """A path is outside the authorized policy."""


class ExternalFileRejectedError(SecurityBoundaryError):
    """An external file failed validation."""


class ExternalUrlRejectedError(SecurityBoundaryError):
    """An external URL failed validation."""


class PluginRejectedError(SecurityBoundaryError):
    """A plugin or manifest is not authorized."""

