"""Tests for platform detection and path resolution."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from ghidractl.platform import Arch, OS, Paths, Platform


class TestPlatformDetect:
    """Test Platform.detect() on different systems."""

    def test_detect_returns_platform(self) -> None:
        p = Platform.detect()
        assert isinstance(p.os, OS)
        assert isinstance(p.arch, Arch)

    @patch("ghidractl.platform._platform.system", return_value="Darwin")
    @patch("ghidractl.platform._platform.machine", return_value="arm64")
    def test_detect_macos_arm64(self, _mock_machine, _mock_system) -> None:
        p = Platform.detect()
        assert p.os == OS.MACOS
        assert p.arch == Arch.ARM64

    @patch("ghidractl.platform._platform.system", return_value="Linux")
    @patch("ghidractl.platform._platform.machine", return_value="x86_64")
    def test_detect_linux_x86_64(self, _mock_machine, _mock_system) -> None:
        p = Platform.detect()
        assert p.os == OS.LINUX
        assert p.arch == Arch.X86_64

    @patch("ghidractl.platform._platform.system", return_value="Windows")
    @patch("ghidractl.platform._platform.machine", return_value="AMD64")
    def test_detect_windows_x86_64(self, _mock_machine, _mock_system) -> None:
        p = Platform.detect()
        assert p.os == OS.WINDOWS
        assert p.arch == Arch.X86_64

    @patch("ghidractl.platform._platform.system", return_value="FreeBSD")
    def test_detect_unsupported_os(self, _mock_system) -> None:
        with pytest.raises(RuntimeError, match="Unsupported operating system"):
            Platform.detect()

    @patch("ghidractl.platform._platform.system", return_value="Linux")
    @patch("ghidractl.platform._platform.machine", return_value="mips")
    def test_detect_unsupported_arch(self, _mock_machine, _mock_system) -> None:
        with pytest.raises(RuntimeError, match="Unsupported architecture"):
            Platform.detect()


class TestPlatformProperties:
    """Test Platform property accessors."""

    def test_ghidra_release_suffix_mac_arm(self) -> None:
        p = Platform(OS.MACOS, Arch.ARM64)
        assert p.ghidra_release_suffix == "mac_arm_64"

    def test_ghidra_release_suffix_linux_x86(self) -> None:
        p = Platform(OS.LINUX, Arch.X86_64)
        assert p.ghidra_release_suffix == "linux_x86_64"

    def test_ghidra_release_suffix_win_x86(self) -> None:
        p = Platform(OS.WINDOWS, Arch.X86_64)
        assert p.ghidra_release_suffix == "win_x86_64"

    def test_adoptium_os(self) -> None:
        assert Platform(OS.MACOS, Arch.ARM64).adoptium_os == "mac"
        assert Platform(OS.LINUX, Arch.X86_64).adoptium_os == "linux"
        assert Platform(OS.WINDOWS, Arch.X86_64).adoptium_os == "windows"

    def test_adoptium_arch(self) -> None:
        assert Platform(OS.MACOS, Arch.ARM64).adoptium_arch == "aarch64"
        assert Platform(OS.LINUX, Arch.X86_64).adoptium_arch == "x64"

    def test_java_executable(self) -> None:
        assert Platform(OS.LINUX, Arch.X86_64).java_executable == "java"
        assert Platform(OS.WINDOWS, Arch.X86_64).java_executable == "java.exe"

    def test_ghidra_launch_script(self) -> None:
        assert Platform(OS.LINUX, Arch.X86_64).ghidra_launch_script == "ghidraRun"
        assert Platform(OS.WINDOWS, Arch.X86_64).ghidra_launch_script == "ghidraRun.bat"

    def test_repr(self) -> None:
        p = Platform(OS.MACOS, Arch.ARM64)
        assert "MACOS" in repr(p)
        assert "ARM64" in repr(p)

    def test_equality(self) -> None:
        a = Platform(OS.MACOS, Arch.ARM64)
        b = Platform(OS.MACOS, Arch.ARM64)
        c = Platform(OS.LINUX, Arch.ARM64)
        assert a == b
        assert a != c
        assert a != "not a platform"

    def test_hash(self) -> None:
        a = Platform(OS.MACOS, Arch.ARM64)
        b = Platform(OS.MACOS, Arch.ARM64)
        assert hash(a) == hash(b)


class TestPaths:
    """Test Paths cross-platform directory resolution."""

    def test_custom_paths(self, tmp_path: Path) -> None:
        p = Paths(data_dir=tmp_path / "d", config_dir=tmp_path / "c")
        assert p.data_dir == tmp_path / "d"
        assert p.config_dir == tmp_path / "c"

    def test_installs_dir(self, tmp_path: Path) -> None:
        p = Paths(data_dir=tmp_path / "d", config_dir=tmp_path / "c")
        assert p.installs_dir == tmp_path / "d" / "installs"

    def test_jdk_dir(self, tmp_path: Path) -> None:
        p = Paths(data_dir=tmp_path / "d", config_dir=tmp_path / "c")
        assert p.jdk_dir == tmp_path / "d" / "jdk"

    def test_registry_file(self, tmp_path: Path) -> None:
        p = Paths(data_dir=tmp_path / "d", config_dir=tmp_path / "c")
        assert p.registry_file == tmp_path / "d" / "registry.toml"

    def test_config_file(self, tmp_path: Path) -> None:
        p = Paths(data_dir=tmp_path / "d", config_dir=tmp_path / "c")
        assert p.config_file == tmp_path / "c" / "config.toml"

    def test_install_dir_for_version(self, tmp_path: Path) -> None:
        p = Paths(data_dir=tmp_path / "d", config_dir=tmp_path / "c")
        assert p.install_dir("11.3") == tmp_path / "d" / "installs" / "11.3"

    def test_ensure_dirs(self, tmp_path: Path) -> None:
        p = Paths(data_dir=tmp_path / "d", config_dir=tmp_path / "c")
        p.ensure_dirs()
        assert p.data_dir.is_dir()
        assert p.config_dir.is_dir()
        assert p.installs_dir.is_dir()
        assert p.jdk_dir.is_dir()
        assert p.cache_dir.is_dir()

    def test_default_paths_use_platformdirs(self) -> None:
        p = Paths()
        assert "ghidractl" in str(p.data_dir)
        assert "ghidractl" in str(p.config_dir)

    def test_custom_installs_dir(self, tmp_path: Path) -> None:
        custom = tmp_path / "my_ghidra"
        p = Paths(data_dir=tmp_path / "d", config_dir=tmp_path / "c", installs_dir=custom)
        assert p.installs_dir == custom
        # Other dirs are unaffected
        assert p.jdk_dir == tmp_path / "d" / "jdk"
        assert p.cache_dir == tmp_path / "d" / "cache"

    def test_install_dir_uses_custom_installs_dir(self, tmp_path: Path) -> None:
        custom = tmp_path / "my_ghidra"
        p = Paths(data_dir=tmp_path / "d", config_dir=tmp_path / "c", installs_dir=custom)
        assert p.install_dir("11.3") == custom / "11.3"

    def test_installs_dir_default_when_none(self, tmp_path: Path) -> None:
        p = Paths(data_dir=tmp_path / "d", config_dir=tmp_path / "c", installs_dir=None)
        assert p.installs_dir == tmp_path / "d" / "installs"

    def test_ensure_dirs_with_custom_installs(self, tmp_path: Path) -> None:
        custom = tmp_path / "my_ghidra"
        p = Paths(data_dir=tmp_path / "d", config_dir=tmp_path / "c", installs_dir=custom)
        p.ensure_dirs()
        assert custom.is_dir()
        assert p.data_dir.is_dir()
        assert p.jdk_dir.is_dir()
