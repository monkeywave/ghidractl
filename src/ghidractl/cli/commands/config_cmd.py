"""ghidractl config commands."""

from __future__ import annotations

import typer

from ghidractl.cli.formatters import console, print_success


def config_show() -> None:
    """Show current configuration."""
    from rich.table import Table

    from ghidractl.config import ConfigManager

    cfg = ConfigManager()
    data = cfg.all()

    table = Table(title="ghidractl Configuration")
    table.add_column("Key", style="cyan")
    table.add_column("Value")

    for key, value in sorted(data.items()):
        # Mask tokens
        display_value = str(value)
        if "token" in key.lower() and value:
            display_value = value[:4] + "..." + value[-4:] if len(str(value)) > 8 else "***"
        # Show effective default for empty install_path
        if key == "install_path" and not value:
            from ghidractl.platform import Paths
            default_dir = Paths().installs_dir
            display_value = f"(default: {default_dir})"
        table.add_row(key, display_value)

    console.print(table)
    console.print(f"\n[dim]Config file: {cfg._paths.config_file}[/]")


def config_set(
    key: str = typer.Argument(help="Configuration key."),
    value: str = typer.Argument(help="Value to set."),
) -> None:
    """Set a configuration value."""
    from ghidractl.config import ConfigManager

    # Type coercion for known boolean keys
    coerced: str | bool = value
    if value.lower() in ("true", "yes", "1"):
        coerced = True
    elif value.lower() in ("false", "no", "0"):
        coerced = False

    cfg = ConfigManager()
    cfg.set(key, coerced)
    print_success(f"{key} = {coerced}")
