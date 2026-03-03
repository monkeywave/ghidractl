"""Validate Java version compatibility with Ghidra."""

from __future__ import annotations

from ghidractl.errors import JavaNotFoundError, JavaVersionError
from ghidractl.ghidra.version_map import required_jdk
from ghidractl.java.detector import JavaInstallation, find_compatible_java
from ghidractl.platform import Platform


def validate_java(
    ghidra_version: str,
    platform: Platform | None = None,
) -> JavaInstallation:
    """Find and validate a Java installation for a Ghidra version.

    Args:
        ghidra_version: Ghidra version string.
        platform: Target platform.

    Returns:
        A compatible JavaInstallation.

    Raises:
        JavaNotFoundError: If no Java is found at all.
        JavaVersionError: If Java is found but version is too low.
    """
    req = required_jdk(ghidra_version)
    platform = platform or Platform.detect()

    java = find_compatible_java(req, platform=platform)
    if java:
        return java

    # Check if there's any Java at all (for better error message)
    from ghidractl.java.detector import detect_java

    all_java = detect_java(platform=platform)
    if all_java:
        best = all_java[0]
        raise JavaVersionError(found=best.version_string, required=req)

    raise JavaNotFoundError(required_version=req)
