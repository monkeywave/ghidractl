"""ghidractl - Ghidra installation manager and Python library."""

from __future__ import annotations

from pathlib import Path

# Re-export java submodule for `ghidractl.java.check()` etc.
from ghidractl import java  # noqa: F401
from ghidractl._version import __version__
from ghidractl.ghidra.installer import install, uninstall, update
from ghidractl.ghidra.launcher import launch
from ghidractl.ghidra.registry import InstalledVersion, VersionRegistry
from ghidractl.ghidra.releases import get_release, latest_version, list_versions
from ghidractl.net.github import GhidraRelease
from ghidractl.platform import Paths


def installed(paths: Paths | None = None) -> list[InstalledVersion]:
    """List installed Ghidra versions."""
    paths = paths or Paths()
    registry = VersionRegistry(paths=paths)
    return registry.list_installed()


def use(version: str, paths: Paths | None = None) -> None:
    """Set the active Ghidra version."""
    paths = paths or Paths()
    registry = VersionRegistry(paths=paths)
    registry.set_active(version)


def run(version: str | None = None, paths: Paths | None = None) -> None:
    """Launch the Ghidra GUI."""
    launch(version=version, paths=paths)


def get_path(version: str | None = None, paths: Paths | None = None) -> Path:
    """Get the install path of a Ghidra version."""
    paths = paths or Paths()
    registry = VersionRegistry(paths=paths)
    if version:
        return registry.get(version).ghidra_path
    return registry.get_active().ghidra_path


__all__ = [
    "__version__",
    "GhidraRelease",
    "InstalledVersion",
    "get_path",
    "get_release",
    "install",
    "installed",
    "java",
    "latest_version",
    "list_versions",
    "run",
    "uninstall",
    "update",
    "use",
]
