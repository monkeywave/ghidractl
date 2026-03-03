"""JDK download and installation via Adoptium."""

from __future__ import annotations

import asyncio
import shutil
import tarfile
import zipfile
from pathlib import Path
from typing import Callable

from ghidractl.errors import JavaInstallError
from ghidractl.ghidra.registry import VersionRegistry
from ghidractl.java.adoptium import AdoptiumRelease, _get_download_info_async
from ghidractl.net.client import HttpClient
from ghidractl.net.download import download_file
from ghidractl.platform import OS, Paths, Platform

ProgressCallback = Callable[[int, int], None]


async def _install_jdk_async(
    version: int = 21,
    platform: Platform | None = None,
    paths: Paths | None = None,
    registry: VersionRegistry | None = None,
    client: HttpClient | None = None,
    progress_callback: ProgressCallback | None = None,
) -> Path:
    """Download and install a JDK from Adoptium.

    Returns:
        Path to the installed JDK home directory.
    """
    platform = platform or Platform.detect()
    paths = paths or Paths()
    registry = registry or VersionRegistry(paths=paths)
    own_client = client is None
    if own_client:
        client = HttpClient()

    try:
        # 1. Get download info
        release = await _get_download_info_async(
            version=version, platform=platform, client=client
        )

        # 2. Download
        paths.ensure_dirs()
        cache_file = paths.cache_dir / release.filename
        await download_file(
            client=client,
            url=release.download_url,
            dest=cache_file,
            expected_sha256=release.checksum if release.checksum else None,
            progress_callback=progress_callback,
        )

        # 3. Extract
        jdk_base = paths.jdk_dir
        if jdk_base.exists():
            shutil.rmtree(jdk_base)
        jdk_base.mkdir(parents=True, exist_ok=True)

        if cache_file.name.endswith(".tar.gz"):
            with tarfile.open(cache_file, "r:gz") as tf:
                tf.extractall(jdk_base)
        elif cache_file.name.endswith(".zip"):
            with zipfile.ZipFile(cache_file, "r") as zf:
                zf.extractall(jdk_base)
        else:
            raise JavaInstallError(f"Unsupported archive format: {cache_file.name}")

        # 4. Find the JDK home directory
        jdk_home = _find_jdk_home(jdk_base, platform)
        if jdk_home is None:
            raise JavaInstallError("Could not locate JDK home directory after extraction")

        # 5. Register
        registry.set_jdk_path(jdk_home)

        # 6. Cleanup
        cache_file.unlink(missing_ok=True)

        return jdk_home

    except JavaInstallError:
        raise
    except Exception as exc:
        raise JavaInstallError(f"JDK installation failed: {exc}") from exc
    finally:
        if own_client:
            await client.close()


def _find_jdk_home(base_dir: Path, platform: Platform) -> Path | None:
    """Find the JDK home directory inside an extracted archive.

    Adoptium archives typically extract to a directory like:
    - jdk-21.0.5+11/ (Linux/Windows)
    - jdk-21.0.5+11/Contents/Home/ (macOS)
    """
    entries = [e for e in base_dir.iterdir() if e.is_dir()]
    if not entries:
        return None

    top = entries[0]

    if platform.os == OS.MACOS:
        # macOS: look for Contents/Home
        contents_home = top / "Contents" / "Home"
        if contents_home.exists():
            return contents_home

    # Check if top-level dir has bin/java
    java_name = platform.java_executable
    if (top / "bin" / java_name).exists():
        return top

    return None


def install_jdk(
    version: int = 21,
    platform: Platform | None = None,
    paths: Paths | None = None,
    progress_callback: ProgressCallback | None = None,
) -> Path:
    """Install a JDK from Adoptium (sync wrapper).

    Args:
        version: JDK major version (e.g., 21).
        platform: Target platform.
        paths: Custom paths.
        progress_callback: Called with (bytes_downloaded, total_bytes).

    Returns:
        Path to the installed JDK home directory.
    """
    return asyncio.run(
        _install_jdk_async(
            version=version,
            platform=platform,
            paths=paths,
            progress_callback=progress_callback,
        )
    )


def get_managed_jdk(paths: Paths | None = None) -> Path | None:
    """Get the path to the managed JDK, if installed.

    Returns:
        Path to JDK home, or None if no managed JDK exists.
    """
    paths = paths or Paths()
    registry = VersionRegistry(paths=paths)
    jdk_path = registry.jdk_path
    if jdk_path and jdk_path.exists():
        return jdk_path
    return None
