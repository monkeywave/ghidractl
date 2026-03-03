"""Track installed Ghidra versions via registry.toml."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w

from ghidractl.errors import NotInstalledError, NoVersionInstalledError
from ghidractl.platform import Paths


@dataclass
class InstalledVersion:
    """A single installed Ghidra version."""

    version: str
    path: str
    installed_at: str = ""
    ghidra_dir: str = ""

    @property
    def install_path(self) -> Path:
        return Path(self.path)

    @property
    def ghidra_path(self) -> Path:
        """Path to the actual Ghidra directory inside the install."""
        if self.ghidra_dir:
            return Path(self.ghidra_dir)
        return self.install_path


class VersionRegistry:
    """CRUD operations on the installed versions registry (registry.toml)."""

    def __init__(self, paths: Paths | None = None) -> None:
        self._paths = paths or Paths()
        self._data: dict[str, Any] = {"active": "", "versions": {}, "jdk_path": ""}
        self._load()

    def _load(self) -> None:
        """Load registry from disk."""
        reg = self._paths.registry_file
        if reg.exists():
            with open(reg, "rb") as f:
                stored = tomllib.load(f)
            self._data.update(stored)

    def _save(self) -> None:
        """Persist registry to disk."""
        self._paths.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self._paths.registry_file, "wb") as f:
            tomli_w.dump(self._data, f)

    @property
    def active_version(self) -> str | None:
        """Currently active Ghidra version, or None."""
        v = self._data.get("active", "")
        return v if v else None

    @property
    def jdk_path(self) -> Path | None:
        """Path to managed JDK, or None."""
        p = self._data.get("jdk_path", "")
        return Path(p) if p else None

    def set_jdk_path(self, path: Path) -> None:
        """Record the managed JDK installation path."""
        self._data["jdk_path"] = str(path)
        self._save()

    def list_installed(self) -> list[InstalledVersion]:
        """List all installed versions, sorted by version string."""
        versions_data = self._data.get("versions", {})
        result = []
        for ver_str, info in versions_data.items():
            result.append(
                InstalledVersion(
                    version=ver_str,
                    path=info.get("path", ""),
                    installed_at=info.get("installed_at", ""),
                    ghidra_dir=info.get("ghidra_dir", ""),
                )
            )
        result.sort(key=lambda v: v.version, reverse=True)
        return result

    def get(self, version: str) -> InstalledVersion:
        """Get an installed version by version string.

        Raises:
            NotInstalledError: If version is not installed.
        """
        versions = self._data.get("versions", {})
        if version not in versions:
            raise NotInstalledError(version)
        info = versions[version]
        return InstalledVersion(
            version=version,
            path=info.get("path", ""),
            installed_at=info.get("installed_at", ""),
            ghidra_dir=info.get("ghidra_dir", ""),
        )

    def get_active(self) -> InstalledVersion:
        """Get the active version.

        Raises:
            NoVersionInstalledError: If no version is active.
        """
        active = self.active_version
        if not active:
            raise NoVersionInstalledError()
        return self.get(active)

    def register(
        self,
        version: str,
        path: Path,
        ghidra_dir: Path | None = None,
        installed_at: str = "",
        set_active: bool = True,
    ) -> None:
        """Register a newly installed Ghidra version."""
        if "versions" not in self._data:
            self._data["versions"] = {}

        self._data["versions"][version] = {
            "path": str(path),
            "ghidra_dir": str(ghidra_dir) if ghidra_dir else "",
            "installed_at": installed_at,
        }

        if set_active or not self.active_version:
            self._data["active"] = version

        self._save()

    def unregister(self, version: str) -> None:
        """Remove a version from the registry.

        Raises:
            NotInstalledError: If version is not in the registry.
        """
        versions = self._data.get("versions", {})
        if version not in versions:
            raise NotInstalledError(version)

        del versions[version]

        if self._data.get("active") == version:
            remaining = list(versions.keys())
            self._data["active"] = remaining[0] if remaining else ""

        self._save()

    def set_active(self, version: str) -> None:
        """Set the active Ghidra version.

        Raises:
            NotInstalledError: If version is not installed.
        """
        if version not in self._data.get("versions", {}):
            raise NotInstalledError(version)
        self._data["active"] = version
        self._save()

    def is_installed(self, version: str) -> bool:
        """Check if a version is installed."""
        return version in self._data.get("versions", {})
