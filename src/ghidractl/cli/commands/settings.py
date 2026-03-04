"""ghidractl settings commands."""

from __future__ import annotations

from pathlib import Path

import typer

from ghidractl.cli.formatters import print_error, print_success
from ghidractl.errors import GhidractlError


def settings_backup(
    output: Path | None = typer.Option(None, "--out", "-o", help="Output ZIP file path."),
) -> None:
    """Backup Ghidra user settings."""
    from ghidractl.ghidra.settings import backup_settings

    try:
        path = backup_settings(output=output)
        print_success(f"Settings backed up to {path}")
    except GhidractlError as exc:
        print_error(str(exc))
        raise typer.Exit(1)


def settings_restore(
    backup: Path = typer.Argument(help="Path to backup ZIP file."),
) -> None:
    """Restore Ghidra settings from a backup."""
    from ghidractl.ghidra.settings import restore_settings

    try:
        path = restore_settings(backup)
        print_success(f"Settings restored to {path}")
    except GhidractlError as exc:
        print_error(str(exc))
        raise typer.Exit(1)
