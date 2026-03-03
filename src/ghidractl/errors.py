"""Exception hierarchy for ghidractl."""

from __future__ import annotations


class GhidractlError(Exception):
    """Base exception for all ghidractl errors."""


# --- Network errors ---

class NetworkError(GhidractlError):
    """Base for network-related errors."""


class DownloadError(NetworkError):
    """Failed to download a file."""


class ChecksumMismatchError(DownloadError):
    """SHA-256 checksum verification failed."""

    def __init__(self, expected: str, actual: str) -> None:
        self.expected = expected
        self.actual = actual
        super().__init__(f"SHA-256 mismatch: expected {expected}, got {actual}")


class GitHubAPIError(NetworkError):
    """GitHub API request failed."""

    def __init__(self, status_code: int, message: str = "") -> None:
        self.status_code = status_code
        super().__init__(f"GitHub API error ({status_code}): {message}")


class RateLimitError(GitHubAPIError):
    """GitHub API rate limit exceeded."""

    def __init__(self, reset_at: int | None = None) -> None:
        self.reset_at = reset_at
        msg = "Rate limit exceeded"
        if reset_at:
            msg += f" (resets at {reset_at})"
        super().__init__(status_code=403, message=msg)


# --- Ghidra errors ---

class GhidraError(GhidractlError):
    """Base for Ghidra-related errors."""


class VersionNotFoundError(GhidraError):
    """Requested Ghidra version not found."""

    def __init__(self, version: str) -> None:
        self.version = version
        super().__init__(f"Ghidra version not found: {version}")


class AlreadyInstalledError(GhidraError):
    """Ghidra version is already installed."""

    def __init__(self, version: str) -> None:
        self.version = version
        super().__init__(f"Ghidra {version} is already installed")


class NotInstalledError(GhidraError):
    """Ghidra version is not installed."""

    def __init__(self, version: str) -> None:
        self.version = version
        super().__init__(f"Ghidra {version} is not installed")


class NoVersionInstalledError(GhidraError):
    """No Ghidra version is installed."""

    def __init__(self) -> None:
        super().__init__("No Ghidra version is installed")


class ExtensionError(GhidraError):
    """Extension installation/management error."""


class LaunchError(GhidraError):
    """Failed to launch Ghidra."""


# --- Java errors ---

class JavaError(GhidractlError):
    """Base for Java-related errors."""


class JavaNotFoundError(JavaError):
    """No compatible Java installation found."""

    def __init__(self, required_version: int | None = None) -> None:
        self.required_version = required_version
        msg = "No compatible Java installation found"
        if required_version:
            msg += f" (JDK {required_version}+ required)"
        super().__init__(msg)


class JavaVersionError(JavaError):
    """Java version does not meet requirements."""

    def __init__(self, found: str, required: int) -> None:
        self.found = found
        self.required = required
        super().__init__(f"Java {found} found, but JDK {required}+ required")


class JavaInstallError(JavaError):
    """Failed to install Java/JDK."""


# --- Config errors ---

class ConfigError(GhidractlError):
    """Configuration file error."""
