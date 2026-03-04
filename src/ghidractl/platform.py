"""OS/architecture detection and cross-platform path resolution."""

from __future__ import annotations

import platform as _platform
from enum import Enum
from pathlib import Path

from platformdirs import user_config_path, user_data_path


class OS(Enum):
    """Supported operating systems."""
    MACOS = "mac"
    LINUX = "linux"
    WINDOWS = "windows"

    @property
    def ghidra_suffix(self) -> str:
        """Suffix used in Ghidra release filenames."""
        return {"mac": "mac_arm_64", "linux": "linux_x86_64", "windows": "win_x86_64"}[self.value]


class Arch(Enum):
    """Supported CPU architectures."""
    X86_64 = "x64"
    ARM64 = "aarch64"

    @property
    def adoptium_name(self) -> str:
        """Architecture name used by Adoptium API."""
        return self.value


class Platform:
    """Detected platform information."""

    def __init__(self, os: OS, arch: Arch) -> None:
        self.os = os
        self.arch = arch

    @classmethod
    def detect(cls) -> Platform:
        """Detect the current platform."""
        system = _platform.system().lower()
        if system == "darwin":
            os = OS.MACOS
        elif system == "linux":
            os = OS.LINUX
        elif system == "windows":
            os = OS.WINDOWS
        else:
            raise RuntimeError(f"Unsupported operating system: {system}")

        machine = _platform.machine().lower()
        if machine in ("x86_64", "amd64"):
            arch = Arch.X86_64
        elif machine in ("arm64", "aarch64"):
            arch = Arch.ARM64
        else:
            raise RuntimeError(f"Unsupported architecture: {machine}")

        return cls(os=os, arch=arch)

    @property
    def ghidra_release_suffix(self) -> str:
        """Build the Ghidra release filename suffix for this platform.

        Examples: mac_arm_64, mac_x86_64, linux_x86_64, linux_arm_64, win_x86_64
        """
        os_map = {OS.MACOS: "mac", OS.LINUX: "linux", OS.WINDOWS: "win"}
        arch_map = {Arch.X86_64: "x86_64", Arch.ARM64: "arm_64"}
        return f"{os_map[self.os]}_{arch_map[self.arch]}"

    @property
    def adoptium_os(self) -> str:
        """OS name for Adoptium API."""
        return {OS.MACOS: "mac", OS.LINUX: "linux", OS.WINDOWS: "windows"}[self.os]

    @property
    def adoptium_arch(self) -> str:
        """Architecture name for Adoptium API."""
        return self.arch.adoptium_name

    @property
    def java_executable(self) -> str:
        """Name of the Java executable."""
        return "java.exe" if self.os == OS.WINDOWS else "java"

    @property
    def ghidra_launch_script(self) -> str:
        """Name of the Ghidra launch script."""
        return "ghidraRun.bat" if self.os == OS.WINDOWS else "ghidraRun"

    def __repr__(self) -> str:
        return f"Platform(os={self.os.name}, arch={self.arch.name})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Platform):
            return NotImplemented
        return self.os == other.os and self.arch == other.arch

    def __hash__(self) -> int:
        return hash((self.os, self.arch))


class Paths:
    """Cross-platform path resolution for ghidractl data and config."""

    APP_NAME = "ghidractl"

    def __init__(
        self,
        data_dir: Path | None = None,
        config_dir: Path | None = None,
        installs_dir: Path | None = None,
    ) -> None:
        self._data_dir = data_dir or user_data_path(self.APP_NAME)
        self._config_dir = config_dir or user_config_path(self.APP_NAME)
        self._installs_dir = installs_dir

    @property
    def data_dir(self) -> Path:
        """Base data directory (installs, registry, managed JDK)."""
        return Path(self._data_dir)

    @property
    def config_dir(self) -> Path:
        """Configuration directory (config.toml)."""
        return Path(self._config_dir)

    @property
    def installs_dir(self) -> Path:
        """Directory containing Ghidra installations."""
        if self._installs_dir is not None:
            return Path(self._installs_dir)
        return self.data_dir / "installs"

    @property
    def jdk_dir(self) -> Path:
        """Directory for managed JDK installation."""
        return self.data_dir / "jdk"

    @property
    def cache_dir(self) -> Path:
        """Directory for download cache."""
        return self.data_dir / "cache"

    @property
    def registry_file(self) -> Path:
        """Path to registry.toml."""
        return self.data_dir / "registry.toml"

    @property
    def config_file(self) -> Path:
        """Path to config.toml."""
        return self.config_dir / "config.toml"

    def install_dir(self, version: str) -> Path:
        """Path to a specific Ghidra version installation."""
        return self.installs_dir / version

    def ensure_dirs(self) -> None:
        """Create all required directories if they don't exist."""
        for d in (self.data_dir, self.config_dir, self.installs_dir, self.jdk_dir, self.cache_dir):
            d.mkdir(parents=True, exist_ok=True)
