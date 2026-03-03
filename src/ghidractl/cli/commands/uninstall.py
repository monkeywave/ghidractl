"""ghidractl uninstall command."""

from __future__ import annotations

import typer

from ghidractl.cli.formatters import print_error, print_success
from ghidractl.errors import GhidractlError


def uninstall(
    version: str = typer.Argument(help="Ghidra version to remove."),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt."),
) -> None:
    """Uninstall a Ghidra version."""
    from ghidractl.ghidra.installer import uninstall as do_uninstall

    if not force:
        confirm = typer.confirm(f"Uninstall Ghidra {version}?")
        if not confirm:
            raise typer.Abort()

    try:
        do_uninstall(version)
        print_success(f"Ghidra {version} uninstalled.")
    except GhidractlError as exc:
        print_error(str(exc))
        raise typer.Exit(1)
