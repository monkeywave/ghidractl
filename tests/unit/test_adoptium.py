"""Tests for Adoptium API client."""

from __future__ import annotations

from ghidractl.java.adoptium import build_download_url
from ghidractl.platform import OS, Arch, Platform


class TestBuildDownloadUrl:
    """Test Adoptium download URL construction."""

    def test_mac_arm64_jdk21(self) -> None:
        p = Platform(OS.MACOS, Arch.ARM64)
        url = build_download_url(21, platform=p)
        assert "mac" in url
        assert "aarch64" in url
        assert "/21/" in url
        assert "jdk" in url

    def test_linux_x86_64_jdk17(self) -> None:
        p = Platform(OS.LINUX, Arch.X86_64)
        url = build_download_url(17, platform=p)
        assert "linux" in url
        assert "x64" in url
        assert "/17/" in url

    def test_windows_x86_64(self) -> None:
        p = Platform(OS.WINDOWS, Arch.X86_64)
        url = build_download_url(21, platform=p)
        assert "windows" in url
        assert "x64" in url

    def test_url_format(self) -> None:
        p = Platform(OS.MACOS, Arch.ARM64)
        url = build_download_url(21, platform=p)
        assert url.startswith("https://api.adoptium.net/v3/binary/latest/")
        assert url.endswith("/jdk/hotspot/normal/eclipse")
