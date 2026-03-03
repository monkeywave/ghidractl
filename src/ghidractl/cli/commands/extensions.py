"""ghidractl ext commands."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from ghidractl.cli.formatters import console, print_error, print_success
from ghidractl.errors import GhidractlError


def ext_list(
    ghidra_version: Optional[str] = typer.Option(None, "--ghidra", help="Ghidra version (uses active if omitted)."),
) -> None:
    """List installed extensions."""
    from rich.table import Table

    from ghidractl.ghidra.extensions import list_extensions

    try:
        exts = list_extensions(version=ghidra_version)

        if not exts:
            console.print("[dim]No extensions found.[/]")
            return

        table = Table(title="Ghidra Extensions")
        table.add_column("Name", style="cyan")
        table.add_column("Version", style="dim")
        table.add_column("Type")
        table.add_column("Description", style="dim", max_width=50)

        for ext in exts:
            ext_type = "[dim]bundled[/]" if ext.bundled else "[green]user[/]"
            table.add_row(ext.name, ext.version, ext_type, ext.description)

        console.print(table)
    except GhidractlError as exc:
        print_error(str(exc))
        raise typer.Exit(1)


def ext_install(
    path: Path = typer.Argument(help="Path to extension ZIP file."),
    ghidra_version: Optional[str] = typer.Option(None, "--ghidra", help="Ghidra version."),
) -> None:
    """Install a Ghidra extension from a ZIP file."""
    from ghidractl.ghidra.extensions import install_extension

    try:
        ext = install_extension(path, version=ghidra_version)
        print_success(f"Extension '{ext.name}' installed.")
    except GhidractlError as exc:
        print_error(str(exc))
        raise typer.Exit(1)


def ext_uninstall(
    name: str = typer.Argument(help="Extension name to remove."),
    ghidra_version: Optional[str] = typer.Option(None, "--ghidra", help="Ghidra version."),
) -> None:
    """Uninstall a Ghidra extension."""
    from ghidractl.ghidra.extensions import uninstall_extension

    try:
        uninstall_extension(name, version=ghidra_version)
        print_success(f"Extension '{name}' uninstalled.")
    except GhidractlError as exc:
        print_error(str(exc))
        raise typer.Exit(1)
