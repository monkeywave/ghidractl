"""Tests for configuration management."""

from __future__ import annotations

from pathlib import Path

import pytest
import tomli_w

from ghidractl.config import ConfigManager
from ghidractl.platform import Paths


class TestConfigManager:
    """Test ConfigManager load/save/access."""

    def test_defaults_when_no_file(self, tmp_paths: Paths) -> None:
        cfg = ConfigManager(paths=tmp_paths)
        assert cfg.github_token == ""
        assert cfg.auto_install_jdk is True
        assert cfg.default_version == "latest"

    def test_load_existing_config(self, tmp_paths: Paths) -> None:
        tmp_paths.config_dir.mkdir(parents=True, exist_ok=True)
        with open(tmp_paths.config_file, "wb") as f:
            tomli_w.dump({"github_token": "ghp_test123", "auto_install_jdk": False}, f)

        cfg = ConfigManager(paths=tmp_paths)
        assert cfg.github_token == "ghp_test123"
        assert cfg.auto_install_jdk is False
        assert cfg.default_version == "latest"  # default preserved

    def test_set_and_save(self, tmp_paths: Paths) -> None:
        cfg = ConfigManager(paths=tmp_paths)
        cfg.set("github_token", "ghp_new_token")

        assert cfg.get("github_token") == "ghp_new_token"
        assert tmp_paths.config_file.exists()

        # Reload and verify persistence
        cfg2 = ConfigManager(paths=tmp_paths)
        assert cfg2.github_token == "ghp_new_token"

    def test_get_with_default(self, tmp_paths: Paths) -> None:
        cfg = ConfigManager(paths=tmp_paths)
        assert cfg.get("nonexistent") is None
        assert cfg.get("nonexistent", "fallback") == "fallback"

    def test_all_returns_copy(self, tmp_paths: Paths) -> None:
        cfg = ConfigManager(paths=tmp_paths)
        data = cfg.all()
        data["github_token"] = "modified"
        assert cfg.github_token == ""  # original unchanged

    def test_save_creates_directory(self, tmp_paths: Paths) -> None:
        cfg = ConfigManager(paths=tmp_paths)
        assert not tmp_paths.config_dir.exists()
        cfg.save()
        assert tmp_paths.config_dir.exists()
        assert tmp_paths.config_file.exists()

    def test_install_path_default(self, tmp_paths: Paths) -> None:
        cfg = ConfigManager(paths=tmp_paths)
        assert cfg.install_path == ""

    def test_set_install_path(self, tmp_paths: Paths) -> None:
        cfg = ConfigManager(paths=tmp_paths)
        cfg.set("install_path", "/tmp/my_ghidra")
        assert cfg.install_path == "/tmp/my_ghidra"

        # Verify persistence
        cfg2 = ConfigManager(paths=tmp_paths)
        assert cfg2.install_path == "/tmp/my_ghidra"
