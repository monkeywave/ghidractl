"""Tests for Ghidra installer permission-setting logic."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from ghidractl.ghidra.installer import _KNOWN_SCRIPTS, _set_executable_permissions


@pytest.mark.skipif(os.name == "nt", reason="Unix-only permission tests")
class TestSetExecutablePermissions:
    """Test _set_executable_permissions behavior."""

    def test_known_scripts_get_executable(self, tmp_path: Path) -> None:
        ghidra_dir = tmp_path / "ghidra_11.3_PUBLIC"
        ghidra_dir.mkdir()

        for script in _KNOWN_SCRIPTS:
            path = ghidra_dir / script
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("#!/bin/bash\n")
            path.chmod(0o644)

        _set_executable_permissions(ghidra_dir)

        for script in _KNOWN_SCRIPTS:
            path = ghidra_dir / script
            mode = path.stat().st_mode
            assert mode & 0o111, f"{script} should have executable bits set"

    def test_sh_files_get_executable(self, tmp_path: Path) -> None:
        ghidra_dir = tmp_path / "ghidra_11.3_PUBLIC"
        ghidra_dir.mkdir()

        nested = ghidra_dir / "Ghidra" / "Features" / "Base" / "data"
        nested.mkdir(parents=True)
        sh_file = nested / "build.sh"
        sh_file.write_text("#!/bin/bash\n")
        sh_file.chmod(0o644)

        _set_executable_permissions(ghidra_dir)

        mode = sh_file.stat().st_mode
        assert mode & 0o111, "Unlisted .sh files should get executable bits"

    def test_missing_scripts_are_skipped(self, tmp_path: Path) -> None:
        ghidra_dir = tmp_path / "ghidra_11.3_PUBLIC"
        ghidra_dir.mkdir()

        # No scripts created — should not raise
        _set_executable_permissions(ghidra_dir)

    def test_preserves_existing_permissions(self, tmp_path: Path) -> None:
        ghidra_dir = tmp_path / "ghidra_11.3_PUBLIC"
        ghidra_dir.mkdir()

        script = ghidra_dir / "ghidraRun"
        script.write_text("#!/bin/bash\n")
        script.chmod(0o640)

        _set_executable_permissions(ghidra_dir)

        mode = script.stat().st_mode & 0o777
        # Original 0o640 (rw-r-----) + 0o111 = 0o751 (rwxr-x--x)
        assert mode == 0o751


class TestSetExecutablePermissionsWindows:
    """Test _set_executable_permissions is a no-op on Windows."""

    def test_noop_on_windows(self, tmp_path: Path) -> None:
        ghidra_dir = tmp_path / "ghidra_11.3_PUBLIC"
        ghidra_dir.mkdir()

        script = ghidra_dir / "ghidraRun"
        script.write_text("#!/bin/bash\n")
        original_mode = script.stat().st_mode

        with patch("ghidractl.ghidra.installer.os.name", "nt"):
            _set_executable_permissions(ghidra_dir)

        assert script.stat().st_mode == original_mode
