"""Ghidra extension management."""

from __future__ import annotations

import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path

from ghidractl.errors import ExtensionError
from ghidractl.ghidra.registry import VersionRegistry
from ghidractl.platform import Paths


@dataclass
class Extension:
    """A Ghidra extension."""

    name: str
    path: Path
    version: str = ""
    description: str = ""
    bundled: bool = False


def _get_ghidra_dir(version: str | None = None, paths: Paths | None = None) -> Path:
    """Get the Ghidra directory for a version."""
    paths = paths or Paths()
    registry = VersionRegistry(paths=paths)
    if version:
        entry = registry.get(version)
    else:
        entry = registry.get_active()
    return entry.ghidra_path


def list_extensions(version: str | None = None, paths: Paths | None = None) -> list[Extension]:
    """List all extensions for a Ghidra installation.

    Args:
        version: Ghidra version (uses active if None).
        paths: Custom paths.

    Returns:
        List of installed and bundled extensions.
    """
    ghidra_dir = _get_ghidra_dir(version, paths)
    extensions: list[Extension] = []

    # Bundled extensions
    bundled_dir = ghidra_dir / "Ghidra" / "Extensions"
    if bundled_dir.exists():
        for ext_dir in bundled_dir.iterdir():
            if ext_dir.is_dir():
                props = _read_extension_properties(ext_dir)
                extensions.append(
                    Extension(
                        name=props.get("name", ext_dir.name),
                        path=ext_dir,
                        version=props.get("version", ""),
                        description=props.get("description", ""),
                        bundled=True,
                    )
                )

    # User-installed extensions
    user_ext_dir = ghidra_dir / "Extensions"
    if user_ext_dir.exists():
        for ext_dir in user_ext_dir.iterdir():
            if ext_dir.is_dir():
                props = _read_extension_properties(ext_dir)
                extensions.append(
                    Extension(
                        name=props.get("name", ext_dir.name),
                        path=ext_dir,
                        version=props.get("version", ""),
                        description=props.get("description", ""),
                        bundled=False,
                    )
                )

    extensions.sort(key=lambda e: e.name.lower())
    return extensions


def install_extension(
    zip_path: Path,
    version: str | None = None,
    paths: Paths | None = None,
) -> Extension:
    """Install an extension from a ZIP file.

    Args:
        zip_path: Path to the extension ZIP.
        version: Ghidra version (uses active if None).
        paths: Custom paths.

    Returns:
        The installed Extension.

    Raises:
        ExtensionError: If installation fails.
    """
    if not zip_path.exists():
        raise ExtensionError(f"Extension ZIP not found: {zip_path}")

    if not zipfile.is_zipfile(zip_path):
        raise ExtensionError(f"Not a valid ZIP file: {zip_path}")

    ghidra_dir = _get_ghidra_dir(version, paths)
    ext_dir = ghidra_dir / "Extensions"
    ext_dir.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            # Determine extension name from ZIP contents
            top_dirs = {name.split("/")[0] for name in zf.namelist() if "/" in name}
            if len(top_dirs) == 1:
                ext_name = top_dirs.pop()
            else:
                ext_name = zip_path.stem

            dest = ext_dir / ext_name
            if dest.exists():
                raise ExtensionError(f"Extension already installed: {ext_name}")

            zf.extractall(ext_dir)

    except ExtensionError:
        raise
    except Exception as exc:
        raise ExtensionError(f"Failed to install extension: {exc}") from exc

    props = _read_extension_properties(dest) if dest.exists() else {}
    return Extension(
        name=props.get("name", ext_name),
        path=dest,
        version=props.get("version", ""),
        description=props.get("description", ""),
        bundled=False,
    )


def uninstall_extension(
    name: str,
    version: str | None = None,
    paths: Paths | None = None,
) -> None:
    """Uninstall an extension by name.

    Args:
        name: Extension name.
        version: Ghidra version (uses active if None).
        paths: Custom paths.

    Raises:
        ExtensionError: If the extension is not found or is bundled.
    """
    ghidra_dir = _get_ghidra_dir(version, paths)
    ext_dir = ghidra_dir / "Extensions" / name

    if not ext_dir.exists():
        raise ExtensionError(f"Extension not found: {name}")

    # Check if bundled
    bundled_dir = ghidra_dir / "Ghidra" / "Extensions" / name
    if bundled_dir.exists():
        raise ExtensionError(f"Cannot uninstall bundled extension: {name}")

    shutil.rmtree(ext_dir)


def _read_extension_properties(ext_dir: Path) -> dict[str, str]:
    """Read extension.properties from an extension directory."""
    props_file = ext_dir / "extension.properties"
    props: dict[str, str] = {}
    if props_file.exists():
        for line in props_file.read_text().splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, _, value = line.partition("=")
                props[key.strip()] = value.strip()
    return props
