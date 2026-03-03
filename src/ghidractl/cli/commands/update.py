"""ghidractl update command."""

from __future__ import annotations

import typer

from ghidractl.cli.formatters import (
    console,
    create_download_progress,
    print_error,
    print_info,
    print_success,
)
from ghidractl.errors import GhidractlError


def update() -> None:
    """Update to the latest Ghidra version."""
    from ghidractl.ghidra.installer import update as do_update

    console.print("Checking for updates...")

    progress = create_download_progress()
    task_id = None

    def on_progress(downloaded: int, total: int) -> None:
        nonlocal task_id
        if task_id is None:
            task_id = progress.add_task("Downloading Ghidra", total=total)
            progress.start()
        progress.update(task_id, completed=downloaded, total=total)

    try:
        result = do_update(progress_callback=on_progress)
        if task_id is not None:
            progress.stop()

        if result is None:
            print_info("Already up to date.")
        else:
            print_success(f"Updated to {result}")
    except GhidractlError as exc:
        if task_id is not None:
            progress.stop()
        print_error(str(exc))
        raise typer.Exit(1)
