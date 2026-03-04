"""Tests for installed version registry."""

from __future__ import annotations

from pathlib import Path

import pytest

from ghidractl.errors import NotInstalledError, NoVersionInstalledError
from ghidractl.ghidra.registry import InstalledVersion, VersionRegistry
from ghidractl.platform import Paths


@pytest.fixture
def registry(tmp_paths: Paths) -> VersionRegistry:
    tmp_paths.ensure_dirs()
    return VersionRegistry(paths=tmp_paths)


class TestVersionRegistry:
    """Test VersionRegistry CRUD operations."""

    def test_empty_registry(self, registry: VersionRegistry) -> None:
        assert registry.list_installed() == []
        assert registry.active_version is None

    def test_register_version(self, registry: VersionRegistry, tmp_paths: Paths) -> None:
        path = tmp_paths.installs_dir / "11.3"
        path.mkdir(parents=True)
        registry.register("11.3", path, installed_at="2025-01-15T00:00:00Z")

        installed = registry.list_installed()
        assert len(installed) == 1
        assert installed[0].version == "11.3"
        assert installed[0].install_path == path
        assert registry.active_version == "11.3"

    def test_register_sets_active(self, registry: VersionRegistry, tmp_paths: Paths) -> None:
        p1 = tmp_paths.installs_dir / "11.2"
        p1.mkdir(parents=True)
        registry.register("11.2", p1)

        p2 = tmp_paths.installs_dir / "11.3"
        p2.mkdir(parents=True)
        registry.register("11.3", p2)

        assert registry.active_version == "11.3"

    def test_get_installed(self, registry: VersionRegistry, tmp_paths: Paths) -> None:
        path = tmp_paths.installs_dir / "11.3"
        path.mkdir(parents=True)
        registry.register("11.3", path)

        v = registry.get("11.3")
        assert v.version == "11.3"

    def test_get_not_installed_raises(self, registry: VersionRegistry) -> None:
        with pytest.raises(NotInstalledError):
            registry.get("99.0")

    def test_unregister(self, registry: VersionRegistry, tmp_paths: Paths) -> None:
        path = tmp_paths.installs_dir / "11.3"
        path.mkdir(parents=True)
        registry.register("11.3", path)
        registry.unregister("11.3")

        assert not registry.is_installed("11.3")
        assert registry.active_version is None

    def test_unregister_switches_active(self, registry: VersionRegistry, tmp_paths: Paths) -> None:
        p1 = tmp_paths.installs_dir / "11.2"
        p1.mkdir(parents=True)
        registry.register("11.2", p1)

        p2 = tmp_paths.installs_dir / "11.3"
        p2.mkdir(parents=True)
        registry.register("11.3", p2)

        registry.unregister("11.3")
        assert registry.active_version == "11.2"

    def test_unregister_not_installed_raises(self, registry: VersionRegistry) -> None:
        with pytest.raises(NotInstalledError):
            registry.unregister("99.0")

    def test_set_active(self, registry: VersionRegistry, tmp_paths: Paths) -> None:
        p1 = tmp_paths.installs_dir / "11.2"
        p1.mkdir(parents=True)
        registry.register("11.2", p1)

        p2 = tmp_paths.installs_dir / "11.3"
        p2.mkdir(parents=True)
        registry.register("11.3", p2)

        registry.set_active("11.2")
        assert registry.active_version == "11.2"

    def test_set_active_not_installed_raises(self, registry: VersionRegistry) -> None:
        with pytest.raises(NotInstalledError):
            registry.set_active("99.0")

    def test_is_installed(self, registry: VersionRegistry, tmp_paths: Paths) -> None:
        assert not registry.is_installed("11.3")
        path = tmp_paths.installs_dir / "11.3"
        path.mkdir(parents=True)
        registry.register("11.3", path)
        assert registry.is_installed("11.3")

    def test_get_active_raises_when_empty(self, registry: VersionRegistry) -> None:
        with pytest.raises(NoVersionInstalledError):
            registry.get_active()

    def test_persistence(self, tmp_paths: Paths) -> None:
        """Registry data persists across instances."""
        tmp_paths.ensure_dirs()
        reg1 = VersionRegistry(paths=tmp_paths)
        path = tmp_paths.installs_dir / "11.3"
        path.mkdir(parents=True)
        reg1.register("11.3", path)

        reg2 = VersionRegistry(paths=tmp_paths)
        assert reg2.is_installed("11.3")
        assert reg2.active_version == "11.3"

    def test_jdk_path(self, registry: VersionRegistry, tmp_paths: Paths) -> None:
        assert registry.jdk_path is None
        jdk = tmp_paths.jdk_dir / "jdk-21"
        registry.set_jdk_path(jdk)
        assert registry.jdk_path == jdk

    def test_ghidra_dir(self, registry: VersionRegistry, tmp_paths: Paths) -> None:
        path = tmp_paths.installs_dir / "11.3"
        path.mkdir(parents=True)
        ghidra = path / "ghidra_11.3_PUBLIC"
        ghidra.mkdir()
        registry.register("11.3", path, ghidra_dir=ghidra)

        v = registry.get("11.3")
        assert v.ghidra_path == ghidra


class TestInstalledVersion:
    """Test InstalledVersion dataclass."""

    def test_install_path(self) -> None:
        v = InstalledVersion(version="11.3", path="/foo/bar")
        assert v.install_path == Path("/foo/bar")

    def test_ghidra_path_with_dir(self) -> None:
        v = InstalledVersion(version="11.3", path="/foo", ghidra_dir="/foo/ghidra")
        assert v.ghidra_path == Path("/foo/ghidra")

    def test_ghidra_path_fallback(self) -> None:
        v = InstalledVersion(version="11.3", path="/foo")
        assert v.ghidra_path == Path("/foo")
