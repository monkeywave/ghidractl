"""TOML configuration management for ghidractl."""

from __future__ import annotations

import sys
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w

from ghidractl.platform import Paths

_DEFAULTS: dict[str, Any] = {
    "github_token": "",
    "auto_install_jdk": True,
    "default_version": "latest",
    "install_path": "",
}


class ConfigManager:
    """Load, save, and access ghidractl configuration from config.toml."""

    def __init__(self, paths: Paths | None = None) -> None:
        self._paths = paths or Paths()
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load config from disk, merging with defaults."""
        self._data = dict(_DEFAULTS)
        cfg = self._paths.config_file
        if cfg.exists():
            with open(cfg, "rb") as f:
                stored = tomllib.load(f)
            self._data.update(stored)

    def save(self) -> None:
        """Persist current config to disk."""
        self._paths.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self._paths.config_file, "wb") as f:
            tomli_w.dump(self._data, f)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a config value and save."""
        self._data[key] = value
        self.save()

    def all(self) -> dict[str, Any]:
        """Return a copy of all config values."""
        return dict(self._data)

    @property
    def github_token(self) -> str:
        """GitHub personal access token for higher rate limits."""
        return self._data.get("github_token", "")

    @property
    def auto_install_jdk(self) -> bool:
        """Whether to automatically prompt for JDK installation."""
        return self._data.get("auto_install_jdk", True)

    @property
    def default_version(self) -> str:
        """Default Ghidra version to install."""
        return self._data.get("default_version", "latest")

    @property
    def install_path(self) -> str:
        """Custom Ghidra install directory (empty = platformdirs default)."""
        return self._data.get("install_path", "")
