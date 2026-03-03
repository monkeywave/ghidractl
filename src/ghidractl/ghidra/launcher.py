"""Launch Ghidra GUI and create platform shortcuts."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from ghidractl.errors import JavaNotFoundError, LaunchError
from ghidractl.ghidra.registry import VersionRegistry
from ghidractl.ghidra.version_map import required_jdk
from ghidractl.java.detector import find_compatible_java
from ghidractl.platform import OS, Paths, Platform


def launch(
    version: str | None = None,
    paths: Paths | None = None,
    platform: Platform | None = None,
    detach: bool = True,
) -> None:
    """Launch the Ghidra GUI.

    Args:
        version: Ghidra version to launch (uses active if None).
        paths: Custom paths.
        platform: Target platform.
        detach: If True, launch in background and return immediately.

    Raises:
        LaunchError: If Ghidra cannot be launched.
    """
    paths = paths or Paths()
    platform = platform or Platform.detect()
    registry = VersionRegistry(paths=paths)

    if version:
        entry = registry.get(version)
    else:
        entry = registry.get_active()

    ghidra_dir = entry.ghidra_path
    launch_script = ghidra_dir / platform.ghidra_launch_script

    if not launch_script.exists():
        raise LaunchError(f"Launch script not found: {launch_script}")

    # Find Java
    req_jdk = required_jdk(entry.version)
    java = find_compatible_java(req_jdk, platform=platform)

    # Also check managed JDK
    if java is None:
        managed_jdk = registry.jdk_path
        if managed_jdk and managed_jdk.exists():
            from ghidractl.java.detector import _check_java_at
            java = _check_java_at(managed_jdk, platform)

    env = os.environ.copy()
    if java:
        env["JAVA_HOME"] = str(java.java_home)

    try:
        if platform.os == OS.WINDOWS:
            cmd = [str(launch_script)]
        else:
            # Ensure script is executable
            launch_script.chmod(launch_script.stat().st_mode | 0o111)
            cmd = [str(launch_script)]

        if detach:
            subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        else:
            subprocess.run(cmd, env=env, check=True)

    except FileNotFoundError as exc:
        raise LaunchError(f"Failed to launch Ghidra: {exc}") from exc
    except subprocess.CalledProcessError as exc:
        raise LaunchError(f"Ghidra exited with error: {exc}") from exc


def create_shortcut(
    version: str | None = None,
    paths: Paths | None = None,
    platform: Platform | None = None,
) -> Path | None:
    """Create a platform-specific shortcut/alias for Ghidra.

    Args:
        version: Ghidra version.
        paths: Custom paths.
        platform: Target platform.

    Returns:
        Path to the created shortcut, or None if not supported.
    """
    paths = paths or Paths()
    platform = platform or Platform.detect()
    registry = VersionRegistry(paths=paths)

    if version:
        entry = registry.get(version)
    else:
        entry = registry.get_active()

    ghidra_dir = entry.ghidra_path

    if platform.os == OS.MACOS:
        return _create_macos_alias(ghidra_dir, entry.version)
    elif platform.os == OS.LINUX:
        return _create_linux_desktop(ghidra_dir, entry.version)

    return None


def _create_macos_alias(ghidra_dir: Path, version: str) -> Path:
    """Create a macOS .command file in /usr/local/bin or ~/bin."""
    bin_dir = Path.home() / "bin"
    bin_dir.mkdir(exist_ok=True)
    script = bin_dir / "ghidra"
    script.write_text(
        f"#!/bin/bash\n"
        f"# Ghidra {version} launcher (created by ghidractl)\n"
        f'exec "{ghidra_dir / "ghidraRun"}" "$@"\n'
    )
    script.chmod(0o755)
    return script


def _create_linux_desktop(ghidra_dir: Path, version: str) -> Path:
    """Create a .desktop file for Linux."""
    desktop_dir = Path.home() / ".local" / "share" / "applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    desktop_file = desktop_dir / "ghidra.desktop"

    icon = ghidra_dir / "docs" / "images" / "GHIDRA_1.png"

    desktop_file.write_text(
        f"[Desktop Entry]\n"
        f"Type=Application\n"
        f"Name=Ghidra {version}\n"
        f"Comment=Ghidra Software Reverse Engineering Suite\n"
        f"Exec={ghidra_dir / 'ghidraRun'}\n"
        f"Icon={icon}\n"
        f"Terminal=false\n"
        f"Categories=Development;ReverseEngineering;\n"
    )
    return desktop_file
