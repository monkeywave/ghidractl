"""Shared test fixtures for ghidractl."""

from __future__ import annotations

from pathlib import Path

import pytest

from ghidractl.platform import Paths


@pytest.fixture
def tmp_paths(tmp_path: Path) -> Paths:
    """Paths instance using temporary directories."""
    return Paths(
        data_dir=tmp_path / "data",
        config_dir=tmp_path / "config",
    )
