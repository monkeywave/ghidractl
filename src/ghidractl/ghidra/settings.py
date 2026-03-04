"""Backup and restore Ghidra user settings."""

from __future__ import annotations

import zipfile
from datetime import datetime, timezone
from pathlib import Path

from ghidractl.errors import GhidraError
from ghidractl.platform import OS, Platform


def _settings_dir(platform: Platform | None = None) -> Path:
    """Locate the Ghidra user settings directory."""
    platform = platform or Platform.detect()

    if platform.os == OS.MACOS:
        return Path.home() / ".ghidra"
    elif platform.os == OS.LINUX:
        return Path.home() / ".ghidra"
    elif platform.os == OS.WINDOWS:
        return Path.home() / "AppData" / "Roaming" / "ghidra"
    else:
        return Path.home() / ".ghidra"


def backup_settings(
    output: Path | None = None,
    platform: Platform | None = None,
) -> Path:
    """Backup Ghidra user settings to a ZIP file.

    Args:
        output: Output ZIP path (auto-generated if None).
        platform: Target platform.

    Returns:
        Path to the created backup ZIP.

    Raises:
        GhidraError: If settings directory doesn't exist.
    """
    settings = _settings_dir(platform)
    if not settings.exists():
        raise GhidraError(f"Ghidra settings directory not found: {settings}")

    if output is None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output = Path.cwd() / f"ghidra_settings_backup_{ts}.zip"

    output.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in settings.rglob("*"):
            if file.is_file():
                arcname = file.relative_to(settings)
                zf.write(file, arcname)

    return output


def restore_settings(
    backup: Path,
    platform: Platform | None = None,
) -> Path:
    """Restore Ghidra settings from a backup ZIP.

    Args:
        backup: Path to the backup ZIP file.
        platform: Target platform.

    Returns:
        Path to the restored settings directory.

    Raises:
        GhidraError: If backup file doesn't exist or is invalid.
    """
    if not backup.exists():
        raise GhidraError(f"Backup file not found: {backup}")

    if not zipfile.is_zipfile(backup):
        raise GhidraError(f"Invalid backup file: {backup}")

    settings = _settings_dir(platform)
    settings.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(backup, "r") as zf:
        zf.extractall(settings)

    return settings
