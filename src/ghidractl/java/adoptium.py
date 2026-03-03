"""Adoptium Temurin API client for JDK downloads."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from ghidractl.net.client import HttpClient
from ghidractl.platform import Platform

_ADOPTIUM_API = "https://api.adoptium.net/v3"


@dataclass
class AdoptiumRelease:
    """An available Adoptium JDK release."""

    version: int
    release_name: str
    download_url: str
    filename: str
    size: int
    checksum: str = ""


async def _get_download_info_async(
    version: int = 21,
    platform: Platform | None = None,
    client: HttpClient | None = None,
) -> AdoptiumRelease:
    """Get download info for a specific JDK version from Adoptium.

    Args:
        version: JDK major version (e.g., 21).
        platform: Target platform.
        client: HTTP client instance.

    Returns:
        AdoptiumRelease with download details.
    """
    platform = platform or Platform.detect()
    own_client = client is None
    if own_client:
        client = HttpClient()

    try:
        url = (
            f"{_ADOPTIUM_API}/assets/latest/{version}/hotspot"
            f"?architecture={platform.adoptium_arch}"
            f"&image_type=jdk"
            f"&os={platform.adoptium_os}"
            f"&vendor=eclipse"
        )
        data = await client.get_json(url)

        if not data:
            raise RuntimeError(f"No Adoptium JDK {version} found for {platform}")

        # Find the best matching binary (prefer .tar.gz on unix, .zip on windows)
        best = None
        for item in data:
            binary = item.get("binary", {})
            pkg = binary.get("package", {})
            name = pkg.get("name", "")

            if platform.os == platform.os.WINDOWS:
                if name.endswith(".zip"):
                    best = item
                    break
            else:
                if name.endswith(".tar.gz"):
                    best = item
                    break

        if best is None:
            best = data[0]

        binary = best.get("binary", {})
        pkg = binary.get("package", {})

        return AdoptiumRelease(
            version=version,
            release_name=best.get("release_name", ""),
            download_url=pkg.get("link", ""),
            filename=pkg.get("name", ""),
            size=pkg.get("size", 0),
            checksum=pkg.get("checksum", ""),
        )
    finally:
        if own_client:
            await client.close()


def get_download_info(
    version: int = 21,
    platform: Platform | None = None,
) -> AdoptiumRelease:
    """Get download info for an Adoptium JDK release (sync wrapper).

    Args:
        version: JDK major version.
        platform: Target platform.

    Returns:
        AdoptiumRelease with download URL and metadata.
    """
    return asyncio.run(_get_download_info_async(version=version, platform=platform))


async def _available_versions_async(
    client: HttpClient | None = None,
) -> list[int]:
    """Fetch available LTS versions from Adoptium."""
    own_client = client is None
    if own_client:
        client = HttpClient()

    try:
        url = f"{_ADOPTIUM_API}/info/available_releases"
        data = await client.get_json(url)
        return data.get("available_lts_releases", [])
    finally:
        if own_client:
            await client.close()


def available_versions() -> list[int]:
    """List available Adoptium LTS versions (sync wrapper)."""
    return asyncio.run(_available_versions_async())


def build_download_url(version: int, platform: Platform | None = None) -> str:
    """Build a direct Adoptium download URL.

    This bypasses the API for simple cases.
    """
    platform = platform or Platform.detect()
    return (
        f"{_ADOPTIUM_API}/binary/latest/{version}/ga"
        f"/{platform.adoptium_os}/{platform.adoptium_arch}"
        f"/jdk/hotspot/normal/eclipse"
    )
