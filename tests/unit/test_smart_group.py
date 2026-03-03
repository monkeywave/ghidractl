"""Tests for SmartGroup 'did you mean?' command suggestions."""

from __future__ import annotations

import click
import pytest

from ghidractl.cli.smart_group import SmartGroup, _collect_commands, _find_suggestions


def _make_app() -> click.Group:
    """Build a minimal click app mirroring ghidractl's command structure."""
    app = SmartGroup(name="ghidractl")

    # Top-level commands
    app.add_command(click.Command("install", callback=lambda: None))
    app.add_command(click.Command("list", callback=lambda: None))
    app.add_command(click.Command("update", callback=lambda: None))
    app.add_command(click.Command("uninstall", callback=lambda: None))
    app.add_command(click.Command("locate", callback=lambda: None))
    app.add_command(click.Command("run", callback=lambda: None))
    app.add_command(click.Command("use", callback=lambda: None))

    # config subgroup
    config_grp = click.Group("config")
    config_grp.add_command(click.Command("show", callback=lambda: None))
    config_grp.add_command(click.Command("set", callback=lambda: None))
    app.add_command(config_grp)

    # java subgroup
    java_grp = click.Group("java")
    java_grp.add_command(click.Command("check", callback=lambda: None))
    java_grp.add_command(click.Command("install", callback=lambda: None))
    java_grp.add_command(click.Command("guide", callback=lambda: None))
    app.add_command(java_grp)

    # ext subgroup
    ext_grp = click.Group("ext")
    ext_grp.add_command(click.Command("list", callback=lambda: None))
    ext_grp.add_command(click.Command("install", callback=lambda: None))
    ext_grp.add_command(click.Command("uninstall", callback=lambda: None))
    app.add_command(ext_grp)

    return app


class TestCollectCommands:
    """Test recursive command collection."""

    def test_collects_top_level_commands(self) -> None:
        app = _make_app()
        cmds = _collect_commands(app)
        assert "install" in cmds
        assert "list" in cmds
        assert "update" in cmds

    def test_collects_nested_commands(self) -> None:
        app = _make_app()
        cmds = _collect_commands(app)
        assert "show" in cmds
        assert cmds["show"] == "config show"
        assert "check" in cmds
        assert cmds["check"] == "java check"

    def test_collects_subgroup_names(self) -> None:
        app = _make_app()
        cmds = _collect_commands(app)
        assert "config" in cmds
        assert "java" in cmds
        assert "ext" in cmds


class TestFindSuggestions:
    """Test fuzzy matching suggestions."""

    def test_suggests_nested_command_for_typo(self) -> None:
        app = _make_app()
        suggestions = _find_suggestions(app, "show")
        assert any("config show" in s for s in suggestions)

    def test_suggests_top_level_command_for_typo(self) -> None:
        app = _make_app()
        suggestions = _find_suggestions(app, "instal")
        assert any("install" in s for s in suggestions)

    def test_no_suggestions_for_gibberish(self) -> None:
        app = _make_app()
        suggestions = _find_suggestions(app, "zzzzxxx")
        assert suggestions == []

    def test_suggests_check_for_chek(self) -> None:
        app = _make_app()
        suggestions = _find_suggestions(app, "chek")
        assert any("java check" in s for s in suggestions)


class TestSmartGroupResolve:
    """Test SmartGroup.resolve_command() error messages."""

    def test_unknown_command_with_suggestion(self) -> None:
        app = _make_app()
        ctx = click.Context(app)
        with pytest.raises(click.UsageError, match="Did you mean"):
            app.resolve_command(ctx, ["show"])

    def test_unknown_command_includes_full_path(self) -> None:
        app = _make_app()
        ctx = click.Context(app)
        with pytest.raises(click.UsageError, match="config show"):
            app.resolve_command(ctx, ["show"])

    def test_unknown_command_no_match(self) -> None:
        app = _make_app()
        ctx = click.Context(app)
        with pytest.raises(click.UsageError, match="No such command 'zzzzxxx'"):
            app.resolve_command(ctx, ["zzzzxxx"])

    def test_valid_command_passes_through(self) -> None:
        app = _make_app()
        ctx = click.Context(app)
        cmd_name, cmd, args = app.resolve_command(ctx, ["install"])
        assert cmd_name == "install"
        assert cmd is not None
