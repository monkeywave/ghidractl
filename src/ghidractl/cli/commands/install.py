"""ghidractl install command."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from ghidractl.cli.formatters import (
    console,
    create_download_progress,
    make_progress_callback,
    print_error,
    print_success,
)
from ghidractl.errors import AlreadyInstalledError, GhidractlError


def install(
    version: str = typer.Argument("latest", help="Ghidra version to install (e.g., '11.3' or 'latest')."),
    install_path: Optional[str] = typer.Option(
        None, "--install-path", "-p",
        help="Custom directory for Ghidra installations.",
    ),
) -> None:
    """Install a Ghidra version."""
    from ghidractl.config import ConfigManager
    from ghidractl.ghidra.installer import install as do_install
    from ghidractl.platform import Paths

    # Resolve install path: CLI flag > config > interactive prompt
    resolved_path: Path | None = None
    if install_path:
        resolved_path = Path(install_path)
    else:
        cfg = ConfigManager()
        if cfg.install_path:
            resolved_path = Path(cfg.install_path)
        else:
            default_path = Paths().installs_dir
            user_input = console.input(
                f"Install directory [dim]\\[{default_path}][/]: "
            ).strip()
            if user_input:
                resolved_path = Path(user_input)

    paths = Paths(installs_dir=resolved_path) if resolved_path else Paths()

    console.print(f"Installing Ghidra [cyan]{version}[/] to [cyan]{paths.installs_dir}[/]...")

    progress = create_download_progress()
    task_id = None

    def on_progress(downloaded: int, total: int) -> None:
        nonlocal task_id
        if task_id is None:
            task_id = progress.add_task("Downloading Ghidra", total=total)
            progress.start()
        progress.update(task_id, completed=downloaded, total=total)

    try:
        path = do_install(version=version, paths=paths, progress_callback=on_progress)
        if task_id is not None:
            progress.stop()
        print_success(f"Ghidra installed to {path}")
    except AlreadyInstalledError as exc:
        if task_id is not None:
            progress.stop()
        print_error(str(exc))
        raise typer.Exit(1)
    except GhidractlError as exc:
        if task_id is not None:
            progress.stop()
        print_error(str(exc))
        raise typer.Exit(1)
