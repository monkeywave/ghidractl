"""Main Typer CLI application for ghidractl."""

from __future__ import annotations

import typer

from ghidractl._version import __version__
from ghidractl.cli.smart_group import SmartGroup

app = typer.Typer(
    name="ghidractl",
    help="Ghidra installation manager and toolchain.",
    no_args_is_help=True,
    rich_markup_mode="rich",
    cls=SmartGroup,
)

# Sub-command groups
java_app = typer.Typer(help="Java/JDK management.", no_args_is_help=True)
ext_app = typer.Typer(help="Ghidra extension management.", no_args_is_help=True)
settings_app = typer.Typer(help="Ghidra settings backup/restore.", no_args_is_help=True)
config_app = typer.Typer(help="ghidractl configuration.", no_args_is_help=True)

app.add_typer(java_app, name="java")
app.add_typer(ext_app, name="ext")
app.add_typer(settings_app, name="settings")
app.add_typer(config_app, name="config")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"ghidractl {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """ghidractl - Ghidra installation manager."""


# Import and register commands
from ghidractl.cli.commands.config_cmd import config_set, config_show  # noqa: E402
from ghidractl.cli.commands.extensions import ext_install, ext_list, ext_uninstall  # noqa: E402
from ghidractl.cli.commands.install import install  # noqa: E402
from ghidractl.cli.commands.java_cmd import java_check, java_guide, java_install  # noqa: E402
from ghidractl.cli.commands.list_cmd import list_cmd  # noqa: E402
from ghidractl.cli.commands.locate import locate  # noqa: E402
from ghidractl.cli.commands.run import run  # noqa: E402
from ghidractl.cli.commands.settings import settings_backup, settings_restore  # noqa: E402
from ghidractl.cli.commands.uninstall import uninstall  # noqa: E402
from ghidractl.cli.commands.update import update  # noqa: E402
from ghidractl.cli.commands.use import use  # noqa: E402

app.command(name="install")(install)
app.command(name="list")(list_cmd)
app.command(name="use")(use)
app.command(name="run")(run)
app.command(name="update")(update)
app.command(name="uninstall")(uninstall)
app.command(name="locate")(locate)

java_app.command(name="check")(java_check)
java_app.command(name="install")(java_install)
java_app.command(name="guide")(java_guide)

ext_app.command(name="list")(ext_list)
ext_app.command(name="install")(ext_install)
ext_app.command(name="uninstall")(ext_uninstall)

settings_app.command(name="backup")(settings_backup)
settings_app.command(name="restore")(settings_restore)

config_app.command(name="show")(config_show)
config_app.command(name="set")(config_set)
