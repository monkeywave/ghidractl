"""Custom Typer group with 'did you mean?' suggestions across nested commands."""

from __future__ import annotations

import difflib

import click
from typer.core import TyperGroup


def _collect_commands(group: click.Group, prefix: str = "") -> dict[str, str]:
    """Recursively collect all commands with their full paths.

    Returns a mapping of {command_name: full_path} for fuzzy matching.
    For nested commands, both the leaf name and full path are indexed.
    """
    commands: dict[str, str] = {}
    for name in group.list_commands(click.Context(group)):
        full_path = f"{prefix} {name}".strip() if prefix else name
        cmd = group.get_command(click.Context(group), name)
        if cmd is None:
            continue
        commands[name] = full_path
        if isinstance(cmd, click.Group):
            nested = _collect_commands(cmd, full_path)
            commands.update(nested)
    return commands


def _find_suggestions(group: click.Group, cmd_name: str) -> list[str]:
    """Find similar commands to the mistyped one."""
    all_commands = _collect_commands(group)
    all_names = list(all_commands.keys())

    matches = difflib.get_close_matches(cmd_name, all_names, n=3, cutoff=0.5)
    return [all_commands[m] for m in matches]


class SmartGroup(TyperGroup):
    """Typer group that suggests similar commands from all levels on typo."""

    def resolve_command(
        self, ctx: click.Context, args: list[str]
    ) -> tuple[str | None, click.Command | None, list[str]]:
        try:
            return super().resolve_command(ctx, args)
        except click.UsageError:
            cmd_name = args[0] if args else ""
            suggestions = _find_suggestions(self, cmd_name)

            if suggestions:
                prog_name = ctx.command_path
                hint_lines = [f"  {prog_name} {s}" for s in suggestions]
                hint = "\n".join(hint_lines)
                ctx.fail(f"No such command '{cmd_name}'.\n\nDid you mean:\n{hint}")
            else:
                ctx.fail(f"No such command '{cmd_name}'.")
