"""Rich terminal output helpers for ghidractl CLI."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.table import Table

if TYPE_CHECKING:
    from ghidractl.ghidra.registry import InstalledVersion
    from ghidractl.java.detector import JavaInstallation
    from ghidractl.net.github import GhidraRelease

console = Console()
error_console = Console(stderr=True)


def print_error(message: str) -> None:
    """Print an error message."""
    error_console.print(f"[bold red]Error:[/] {message}")


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[bold green]OK:[/] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[dim]{message}[/]")


def print_version_table(
    releases: list["GhidraRelease"],
    installed_versions: set[str] | None = None,
    active_version: str | None = None,
) -> None:
    """Print a table of Ghidra versions."""
    installed_versions = installed_versions or set()

    table = Table(title="Ghidra Versions")
    table.add_column("Version", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Released", style="dim")
    table.add_column("Tag")

    for rel in releases:
        status = ""
        if rel.version in installed_versions:
            if rel.version == active_version:
                status = "[bold green]* active[/]"
            else:
                status = "[green]installed[/]"

        table.add_row(
            rel.version,
            status,
            rel.published_at[:10] if rel.published_at else "",
            rel.tag,
        )

    console.print(table)


def print_installed_table(
    installed: list["InstalledVersion"],
    active_version: str | None = None,
) -> None:
    """Print a table of installed Ghidra versions."""
    if not installed:
        console.print("[dim]No Ghidra versions installed.[/]")
        return

    table = Table(title="Installed Ghidra Versions")
    table.add_column("Version", style="cyan")
    table.add_column("Active", style="green")
    table.add_column("Path", style="dim")
    table.add_column("Installed", style="dim")

    for v in installed:
        active = "[bold green]*[/]" if v.version == active_version else ""
        table.add_row(v.version, active, str(v.ghidra_path), v.installed_at[:10] if v.installed_at else "")

    console.print(table)


def print_java_status(java: "JavaInstallation | None") -> None:
    """Print Java installation status."""
    if java is None:
        panel = Panel(
            "[red]No compatible Java installation found.[/]\n"
            "Run [bold]ghidractl java install[/] or [bold]ghidractl java guide[/]",
            title="Java Status",
            border_style="red",
        )
    else:
        panel = Panel(
            f"[green]Java found[/]\n"
            f"  Version: [cyan]{java.version_string}[/]\n"
            f"  Path:    [dim]{java.java_home}[/]\n"
            f"  JDK:     {'Yes' if java.is_jdk else 'No (JRE only)'}",
            title="Java Status",
            border_style="green",
        )
    console.print(panel)


def create_download_progress() -> Progress:
    """Create a Rich progress bar for downloads."""
    return Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
    )


def make_progress_callback(progress: Progress, task_id: int):
    """Create a callback function for download progress updates."""
    def callback(downloaded: int, total: int) -> None:
        if total > 0:
            progress.update(task_id, completed=downloaded, total=total)
    return callback
