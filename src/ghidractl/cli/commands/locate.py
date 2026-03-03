"""ghidractl locate command."""

from __future__ import annotations

from typing import Optional

import typer

from ghidractl.cli.formatters import print_error
from ghidractl.errors import GhidractlError


def locate(
    version: Optional[str] = typer.Argument(None, help="Ghidra version (uses active if omitted)."),
) -> None:
    """Print the install path of a Ghidra version."""
    from ghidractl.ghidra.registry import VersionRegistry
    from ghidractl.platform import Paths

    try:
        paths = Paths()
        registry = VersionRegistry(paths=paths)

        if version:
            entry = registry.get(version)
        else:
            entry = registry.get_active()

        typer.echo(str(entry.ghidra_path))
    except GhidractlError as exc:
        print_error(str(exc))
        raise typer.Exit(1)
