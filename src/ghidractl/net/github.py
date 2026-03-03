"""GitHub releases API wrapper for NationalSecurityAgency/ghidra."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from packaging.version import Version

from ghidractl.errors import VersionNotFoundError

_REPO = "NationalSecurityAgency/ghidra"
_RELEASES_URL = f"https://api.github.com/repos/{_REPO}/releases"
_SHA256_PATTERN = re.compile(r"SHA.?256[:\s]*`?([a-fA-F0-9]{64})`?", re.IGNORECASE)


@dataclass
class GhidraRelease:
    """A single Ghidra release from GitHub."""

    tag: str
    version: str
    name: str
    published_at: str
    assets: list[ReleaseAsset] = field(default_factory=list)
    body: str = ""
    prerelease: bool = False

    @property
    def parsed_version(self) -> Version:
        return Version(self.version)

    @property
    def sha256(self) -> str | None:
        """Extract SHA-256 hash from release body."""
        if not self.body:
            return None
        match = _SHA256_PATTERN.search(self.body)
        return match.group(1).lower() if match else None

    def asset_for_platform(self, suffix: str) -> ReleaseAsset | None:
        """Find the asset matching a platform suffix like 'mac_arm_64'.

        Falls back to the first ZIP asset if no platform-specific match is
        found (Ghidra releases are typically universal/platform-independent).
        """
        for asset in self.assets:
            if suffix in asset.name and asset.name.endswith(".zip"):
                return asset
        # Ghidra ZIPs are universal (Java-based) — fall back to first ZIP
        return self.default_asset()

    def default_asset(self) -> ReleaseAsset | None:
        """Return the first ZIP asset (for universal/platform-independent releases)."""
        for asset in self.assets:
            if asset.name.endswith(".zip"):
                return asset
        return None


@dataclass
class ReleaseAsset:
    """A downloadable asset attached to a release."""

    name: str
    url: str
    size: int
    content_type: str = ""


def parse_release(data: dict[str, Any]) -> GhidraRelease:
    """Parse a GitHub API release response into a GhidraRelease."""
    tag = data.get("tag_name", "")
    version = tag.lstrip("Ghidra_").split("_build")[0] if "Ghidra_" in tag else tag.lstrip("v")

    assets = [
        ReleaseAsset(
            name=a["name"],
            url=a["browser_download_url"],
            size=a["size"],
            content_type=a.get("content_type", ""),
        )
        for a in data.get("assets", [])
    ]

    return GhidraRelease(
        tag=tag,
        version=version,
        name=data.get("name", ""),
        published_at=data.get("published_at", ""),
        assets=assets,
        body=data.get("body", ""),
        prerelease=data.get("prerelease", False),
    )


async def fetch_releases(client: Any, include_prerelease: bool = False) -> list[GhidraRelease]:
    """Fetch all Ghidra releases from GitHub API.

    Args:
        client: An HttpClient instance.
        include_prerelease: Whether to include pre-release versions.

    Returns:
        List of releases sorted by version (newest first).
    """
    releases: list[GhidraRelease] = []
    page = 1

    while True:
        url = f"{_RELEASES_URL}?per_page=30&page={page}"
        data = await client.get_json(url)

        if not data:
            break

        for item in data:
            rel = parse_release(item)
            if not include_prerelease and rel.prerelease:
                continue
            releases.append(rel)

        if len(data) < 30:
            break
        page += 1

    releases.sort(key=lambda r: r.parsed_version, reverse=True)
    return releases


async def fetch_release(client: Any, version: str) -> GhidraRelease:
    """Fetch a specific Ghidra release by version string.

    Args:
        client: An HttpClient instance.
        version: Version string like "11.3" or "latest".

    Returns:
        The matching GhidraRelease.

    Raises:
        VersionNotFoundError: If the version doesn't exist.
    """
    all_releases = await fetch_releases(client)

    if not all_releases:
        raise VersionNotFoundError(version)

    if version == "latest":
        return all_releases[0]

    for rel in all_releases:
        if rel.version == version:
            return rel

    raise VersionNotFoundError(version)
