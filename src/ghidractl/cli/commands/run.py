"""ghidractl run command."""

from __future__ import annotations

from typing import Optional

import typer

from ghidractl.cli.formatters import console, print_error
from ghidractl.errors import GhidractlError


def run(
    version: Optional[str] = typer.Argument(None, help="Ghidra version to launch (uses active if omitted)."),
) -> None:
    """Launch the Ghidra GUI."""
    from ghidractl.ghidra.launcher import launch

    try:
        console.print(f"Launching Ghidra{' ' + version if version else ''}...")
        launch(version=version)
        console.print("[green]Ghidra launched.[/]")
    except GhidractlError as exc:
        print_error(str(exc))
        raise typer.Exit(1)
