"""ghidractl java commands."""

from __future__ import annotations

import typer

from ghidractl.cli.formatters import (
    console,
    create_download_progress,
    print_error,
    print_java_status,
    print_success,
)
from ghidractl.errors import GhidractlError


def java_check() -> None:
    """Show Java installation status."""
    import ghidractl.java as java_mod

    java = java_mod.check()
    print_java_status(java)


def java_install(
    version: int = typer.Option(21, "--version", "-v", help="JDK major version to install."),
) -> None:
    """Install a JDK via Adoptium Temurin."""
    from ghidractl.java.installer import install_jdk

    console.print(f"Installing JDK {version} via Adoptium...")

    progress = create_download_progress()
    task_id = None

    def on_progress(downloaded: int, total: int) -> None:
        nonlocal task_id
        if task_id is None:
            task_id = progress.add_task(f"Downloading JDK {version}", total=total)
            progress.start()
        progress.update(task_id, completed=downloaded, total=total)

    try:
        path = install_jdk(version=version, progress_callback=on_progress)
        if task_id is not None:
            progress.stop()
        print_success(f"JDK {version} installed to {path}")
    except GhidractlError as exc:
        if task_id is not None:
            progress.stop()
        print_error(str(exc))
        raise typer.Exit(1)


def java_guide() -> None:
    """Print manual Java installation instructions."""
    import ghidractl.java as java_mod

    console.print(java_mod.guide())
