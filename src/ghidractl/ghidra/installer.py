"""Ghidra installation pipeline: resolve -> download -> verify -> extract -> register."""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ghidractl.errors import (
    AlreadyInstalledError,
    DownloadError,
    GhidraError,
    NotInstalledError,
)
from ghidractl.ghidra.registry import VersionRegistry
from ghidractl.ghidra.version_map import required_jdk
from ghidractl.net.client import HttpClient
from ghidractl.net.download import ProgressCallback, download_file
from ghidractl.net.github import GhidraRelease, fetch_release
from ghidractl.platform import Paths, Platform

logger = logging.getLogger(__name__)

_KNOWN_SCRIPTS = [
    "ghidraRun",
    "support/analyzeHeadless",
    "support/launch.sh",
    "support/sleigh",
    "server/ghidraSvr",
    "server/svrInstall",
    "server/svrUninstall",
]


async def _install_async(
    version: str = "latest",
    platform: Platform | None = None,
    paths: Paths | None = None,
    registry: VersionRegistry | None = None,
    client: HttpClient | None = None,
    progress_callback: ProgressCallback | None = None,
    skip_java_check: bool = False,
) -> Path:
    """Async implementation of the install pipeline."""
    platform = platform or Platform.detect()
    paths = paths or Paths()
    registry = registry or VersionRegistry(paths=paths)
    own_client = client is None
    if own_client:
        client = HttpClient()

    try:
        # 1. Resolve version
        release = await fetch_release(client, version)

        # 2. Check if already installed
        if registry.is_installed(release.version):
            raise AlreadyInstalledError(release.version)

        # 3. Find platform asset (falls back to universal ZIP via default_asset)
        asset = release.asset_for_platform(platform.ghidra_release_suffix)
        if asset is None:
            raise GhidraError(
                f"No downloadable ZIP asset found in Ghidra {release.version}"
            )

        # 4. Download
        paths.ensure_dirs()
        cache_file = paths.cache_dir / asset.name
        await download_file(
            client=client,
            url=asset.url,
            dest=cache_file,
            expected_sha256=release.sha256,
            progress_callback=progress_callback,
        )

        # 5. Extract
        install_dir = paths.install_dir(release.version)
        install_dir.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(cache_file, "r") as zf:
                zf.extractall(install_dir)
        except (zipfile.BadZipFile, OSError) as exc:
            shutil.rmtree(install_dir, ignore_errors=True)
            raise GhidraError(f"Extraction failed for Ghidra {release.version}: {exc}") from exc

        # Find the actual ghidra directory inside the extraction
        ghidra_dir = _find_ghidra_dir(install_dir)
        if ghidra_dir is None:
            shutil.rmtree(install_dir, ignore_errors=True)
            raise GhidraError(
                f"Extracted archive for Ghidra {release.version} does not contain "
                f"a valid Ghidra directory (missing ghidraRun)"
            )

        # Set executable permissions on scripts (Unix only)
        _set_executable_permissions(ghidra_dir)

        # 6. Verify SHA-256 if available
        if release.sha256 is None:
            logger.warning("No SHA-256 hash in release notes for Ghidra %s — skipping verification", release.version)

        # 7. Register
        registry.register(
            version=release.version,
            path=install_dir,
            ghidra_dir=ghidra_dir,
            installed_at=datetime.now(timezone.utc).isoformat(),
            set_active=True,
        )

        # 8. Cleanup cache
        cache_file.unlink(missing_ok=True)

        return ghidra_dir

    finally:
        if own_client:
            await client.close()


def _find_ghidra_dir(install_dir: Path) -> Path | None:
    """Find the actual Ghidra directory inside an extracted ZIP.

    Ghidra ZIPs typically contain a single top-level directory like
    'ghidra_11.3_PUBLIC'.
    """
    entries = list(install_dir.iterdir())
    if len(entries) == 1 and entries[0].is_dir():
        candidate = entries[0]
        if (candidate / "ghidraRun").exists() or (candidate / "ghidraRun.bat").exists():
            return candidate
    return None


def _set_executable_permissions(ghidra_dir: Path) -> None:
    """Set executable permissions on Ghidra scripts (Unix only)."""
    if os.name == "nt":
        return

    for script in _KNOWN_SCRIPTS:
        path = ghidra_dir / script
        if path.is_file():
            path.chmod(path.stat().st_mode | 0o111)

    # Catch any .sh files not in the known list
    for sh_file in ghidra_dir.rglob("*.sh"):
        if sh_file.is_file():
            sh_file.chmod(sh_file.stat().st_mode | 0o111)

    logger.debug("Set executable permissions on Ghidra scripts in %s", ghidra_dir)


def install(
    version: str = "latest",
    platform: Platform | None = None,
    paths: Paths | None = None,
    progress_callback: ProgressCallback | None = None,
) -> Path:
    """Install a Ghidra version.

    Args:
        version: Version to install ("latest" or specific like "11.3").
        platform: Target platform (auto-detected if None).
        paths: Custom paths (defaults if None).
        progress_callback: Called with (bytes_downloaded, total_bytes).

    Returns:
        Path to the installed Ghidra directory.

    Raises:
        AlreadyInstalledError: If the version is already installed.
        VersionNotFoundError: If the version doesn't exist.
        DownloadError: If the download fails.
    """
    return asyncio.run(
        _install_async(
            version=version,
            platform=platform,
            paths=paths,
            progress_callback=progress_callback,
        )
    )


def uninstall(version: str, paths: Paths | None = None) -> None:
    """Uninstall a Ghidra version.

    Args:
        version: Version to remove.
        paths: Custom paths (defaults if None).

    Raises:
        NotInstalledError: If the version is not installed.
    """
    paths = paths or Paths()
    registry = VersionRegistry(paths=paths)
    entry = registry.get(version)

    # Remove files
    install_path = entry.install_path
    if install_path.exists():
        shutil.rmtree(install_path)

    # Remove from registry
    registry.unregister(version)


async def _update_async(
    platform: Platform | None = None,
    paths: Paths | None = None,
    client: HttpClient | None = None,
    progress_callback: ProgressCallback | None = None,
) -> Path | None:
    """Check for updates and install if available."""
    platform = platform or Platform.detect()
    paths = paths or Paths()
    registry = VersionRegistry(paths=paths)
    own_client = client is None
    if own_client:
        client = HttpClient()

    try:
        release = await fetch_release(client, "latest")

        if registry.is_installed(release.version):
            return None  # Already up to date

        return await _install_async(
            version=release.version,
            platform=platform,
            paths=paths,
            registry=registry,
            client=client,
            progress_callback=progress_callback,
        )
    finally:
        if own_client:
            await client.close()


def update(
    platform: Platform | None = None,
    paths: Paths | None = None,
    progress_callback: ProgressCallback | None = None,
) -> Path | None:
    """Update to the latest Ghidra version.

    Returns:
        Path to new installation, or None if already up to date.
    """
    return asyncio.run(
        _update_async(
            platform=platform,
            paths=paths,
            progress_callback=progress_callback,
        )
    )
