"""Tests for GitHub releases parsing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ghidractl.net.github import GhidraRelease, ReleaseAsset, parse_release


@pytest.fixture
def releases_data() -> list[dict]:
    fixtures = Path(__file__).parent.parent / "fixtures" / "releases_response.json"
    with open(fixtures) as f:
        return json.load(f)


class TestParseRelease:
    """Test parse_release from GitHub API data."""

    def test_parse_basic_fields(self, releases_data: list[dict]) -> None:
        rel = parse_release(releases_data[0])
        assert rel.tag == "Ghidra_11.3_build"
        assert rel.version == "11.3"
        assert rel.name == "Ghidra 11.3"
        assert rel.prerelease is False

    def test_parse_version_from_tag(self, releases_data: list[dict]) -> None:
        rel = parse_release(releases_data[1])
        assert rel.version == "11.2.1"

    def test_parse_assets(self, releases_data: list[dict]) -> None:
        rel = parse_release(releases_data[0])
        assert len(rel.assets) == 1
        assert rel.assets[0].name == "ghidra_11.3_PUBLIC_20250115.zip"
        assert rel.assets[0].size == 400000000

    def test_sha256_extraction(self, releases_data: list[dict]) -> None:
        rel = parse_release(releases_data[0])
        assert rel.sha256 == "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

    def test_sha256_without_backticks(self, releases_data: list[dict]) -> None:
        rel = parse_release(releases_data[1])
        assert rel.sha256 == "1111111111111111111111111111111111111111111111111111111111111111"

    def test_sha256_missing(self, releases_data: list[dict]) -> None:
        rel = parse_release(releases_data[2])
        assert rel.sha256 is None

    def test_asset_for_platform_universal_fallback(self, releases_data: list[dict]) -> None:
        """Universal ZIPs (no platform suffix) are returned via fallback."""
        rel = parse_release(releases_data[0])
        asset = rel.asset_for_platform("mac_arm_64")
        assert asset is not None
        assert asset.name == "ghidra_11.3_PUBLIC_20250115.zip"

    def test_asset_for_platform_no_assets(self, releases_data: list[dict]) -> None:
        """Release with no assets returns None."""
        rel = parse_release(releases_data[2])
        assert rel.asset_for_platform("mac_arm_64") is None

    def test_default_asset(self, releases_data: list[dict]) -> None:
        """default_asset() returns the first ZIP for universal releases."""
        rel = parse_release(releases_data[0])
        asset = rel.default_asset()
        assert asset is not None
        assert asset.name == "ghidra_11.3_PUBLIC_20250115.zip"

    def test_default_asset_no_assets(self, releases_data: list[dict]) -> None:
        """default_asset() returns None when no assets exist."""
        rel = parse_release(releases_data[2])
        assert rel.default_asset() is None

    def test_default_asset_non_zip(self) -> None:
        """default_asset() skips non-ZIP assets."""
        rel = GhidraRelease(
            tag="test",
            version="1.0",
            name="Test",
            published_at="2025-01-01",
            assets=[ReleaseAsset(name="notes.txt", url="http://x", size=100)],
        )
        assert rel.default_asset() is None

    def test_parsed_version(self, releases_data: list[dict]) -> None:
        rel = parse_release(releases_data[0])
        from packaging.version import Version
        assert rel.parsed_version == Version("11.3")
