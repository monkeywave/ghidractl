"""ghidractl list command."""

from __future__ import annotations

import typer

from ghidractl.cli.formatters import (
    console,
    print_error,
    print_installed_table,
    print_version_table,
)
from ghidractl.errors import GhidractlError


def list_cmd(
    all_versions: bool = typer.Option(
        False, "--all", "-a",
        help="Show all available versions from GitHub.",
    ),
) -> None:
    """List Ghidra versions."""
    from ghidractl.ghidra.registry import VersionRegistry
    from ghidractl.platform import Paths

    try:
        paths = Paths()
        registry = VersionRegistry(paths=paths)
        installed = registry.list_installed()
        active = registry.active_version

        if all_versions:
            from ghidractl.ghidra.releases import list_versions

            with console.status("Fetching releases from GitHub..."):
                releases = list_versions()

            installed_set = {v.version for v in installed}
            print_version_table(releases, installed_versions=installed_set, active_version=active)
        else:
            print_installed_table(installed, active_version=active)

    except GhidractlError as exc:
        print_error(str(exc))
        raise typer.Exit(1)
