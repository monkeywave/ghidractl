"""ghidractl use command."""

from __future__ import annotations

import typer

from ghidractl.cli.formatters import print_error, print_success
from ghidractl.errors import GhidractlError


def use(
    version: str = typer.Argument(help="Ghidra version to set as active."),
) -> None:
    """Set the active Ghidra version."""
    from ghidractl.ghidra.registry import VersionRegistry
    from ghidractl.platform import Paths

    try:
        paths = Paths()
        registry = VersionRegistry(paths=paths)
        registry.set_active(version)
        print_success(f"Active version set to {version}")
    except GhidractlError as exc:
        print_error(str(exc))
        raise typer.Exit(1)
