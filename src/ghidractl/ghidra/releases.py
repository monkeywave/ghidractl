"""High-level Ghidra release discovery using GitHub API."""

from __future__ import annotations

import asyncio
from typing import Any

from ghidractl.net.client import HttpClient
from ghidractl.net.github import GhidraRelease, fetch_release, fetch_releases


async def _list_versions_async(
    client: HttpClient | None = None,
    include_prerelease: bool = False,
) -> list[GhidraRelease]:
    """Async implementation of list_versions."""
    own_client = client is None
    if own_client:
        client = HttpClient()
    try:
        return await fetch_releases(client, include_prerelease=include_prerelease)
    finally:
        if own_client:
            await client.close()


async def _latest_version_async(
    client: HttpClient | None = None,
) -> GhidraRelease:
    """Async implementation of latest_version."""
    own_client = client is None
    if own_client:
        client = HttpClient()
    try:
        return await fetch_release(client, "latest")
    finally:
        if own_client:
            await client.close()


async def _get_release_async(
    version: str,
    client: HttpClient | None = None,
) -> GhidraRelease:
    """Async implementation of get_release."""
    own_client = client is None
    if own_client:
        client = HttpClient()
    try:
        return await fetch_release(client, version)
    finally:
        if own_client:
            await client.close()


def list_versions(include_prerelease: bool = False) -> list[GhidraRelease]:
    """List all available Ghidra versions from GitHub.

    Returns:
        List of GhidraRelease sorted newest first.
    """
    return asyncio.run(_list_versions_async(include_prerelease=include_prerelease))


def latest_version() -> GhidraRelease:
    """Get the latest Ghidra release.

    Returns:
        The newest stable GhidraRelease.
    """
    return asyncio.run(_latest_version_async())


def get_release(version: str) -> GhidraRelease:
    """Get a specific Ghidra release by version.

    Args:
        version: Version string like "11.3" or "latest".

    Returns:
        The matching GhidraRelease.
    """
    return asyncio.run(_get_release_async(version))
