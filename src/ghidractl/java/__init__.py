"""Java/JDK management for ghidractl."""

from __future__ import annotations

from pathlib import Path

from ghidractl.java.detector import (
    JavaInstallation,
    detect_java,
)
from ghidractl.java.detector import (
    find_compatible_java as find_compatible_java,
)
from ghidractl.java.installer import (
    get_managed_jdk as get_managed_jdk,
)
from ghidractl.java.installer import (
    install_jdk,
)
from ghidractl.java.validator import validate_java


def check(ghidra_version: str | None = None) -> JavaInstallation | None:
    """Check for a compatible Java installation.

    Args:
        ghidra_version: If provided, check compatibility with this Ghidra version.

    Returns:
        The best JavaInstallation found, or None.
    """
    if ghidra_version:
        try:
            return validate_java(ghidra_version)
        except Exception:
            return None

    installations = detect_java()
    return installations[0] if installations else None


def install(version: int = 21, **kwargs) -> Path:
    """Install a JDK via Adoptium.

    Args:
        version: JDK major version (default: 21).

    Returns:
        Path to installed JDK home.
    """
    return install_jdk(version=version, **kwargs)


def guide() -> str:
    """Return manual JDK installation instructions."""
    return (
        "Manual JDK Installation Guide\n"
        "==============================\n\n"
        "Option 1: Adoptium Temurin (Recommended)\n"
        "  Visit: https://adoptium.net/temurin/releases/\n"
        "  Download JDK 21 for your platform.\n\n"
        "Option 2: Package Manager\n"
        "  macOS:   brew install --cask temurin@21\n"
        "  Ubuntu:  apt install temurin-21-jdk\n"
        "  Fedora:  dnf install java-21-openjdk-devel\n"
        "  Windows: winget install EclipseAdoptium.Temurin.21.JDK\n\n"
        "After installing, set JAVA_HOME and ensure java is on PATH.\n"
    )
