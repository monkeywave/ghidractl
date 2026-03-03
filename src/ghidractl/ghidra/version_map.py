"""Mapping of Ghidra versions to JDK requirements."""

from __future__ import annotations

from packaging.version import Version

# (min_ghidra_version, required_jdk_version)
# Ordered from newest to oldest - first match wins
_VERSION_JDK_MAP: list[tuple[str, int]] = [
    ("11.0", 21),
    ("10.4", 17),
    ("10.0", 17),
    ("9.0", 11),
]

# Default JDK version for unknown/future Ghidra versions
_DEFAULT_JDK = 21


def required_jdk(ghidra_version: str) -> int:
    """Get the minimum required JDK version for a Ghidra version.

    Args:
        ghidra_version: Ghidra version string like "11.3" or "10.4.1".

    Returns:
        Minimum JDK major version (e.g., 21, 17, 11).
    """
    try:
        gv = Version(ghidra_version)
    except Exception:
        return _DEFAULT_JDK

    for min_ver_str, jdk_ver in _VERSION_JDK_MAP:
        if gv >= Version(min_ver_str):
            return jdk_ver

    return _DEFAULT_JDK


def recommended_jdk(ghidra_version: str | None = None) -> int:
    """Get the recommended JDK version to install.

    For latest Ghidra, this is JDK 21. Delegates to required_jdk if a
    specific Ghidra version is given.

    Args:
        ghidra_version: Optional Ghidra version string.

    Returns:
        Recommended JDK major version.
    """
    if ghidra_version:
        return required_jdk(ghidra_version)
    return _DEFAULT_JDK


def is_jdk_compatible(java_version: int, ghidra_version: str) -> bool:
    """Check if a JDK version is compatible with a Ghidra version.

    Args:
        java_version: JDK major version (e.g., 21).
        ghidra_version: Ghidra version string.

    Returns:
        True if the JDK meets the minimum requirement.
    """
    return java_version >= required_jdk(ghidra_version)
