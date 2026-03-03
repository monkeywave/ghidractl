"""Detect existing Java installations on the system."""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ghidractl.platform import Platform


@dataclass
class JavaInstallation:
    """A detected Java installation."""

    path: Path
    version_string: str
    major_version: int
    is_jdk: bool = True

    @property
    def java_home(self) -> Path:
        return self.path

    @property
    def java_executable(self) -> Path:
        return self.path / "bin" / "java"


_VERSION_PATTERN = re.compile(r'"(\d+)(?:\.(\d+))?(?:\.(\d+))?')


def parse_java_version(output: str) -> int | None:
    """Parse the major version from `java -version` output.

    Java version strings changed format:
    - Java 8: "1.8.0_xxx"
    - Java 9+: "9.0.x", "11.0.x", "17.0.x", "21.0.x"
    """
    match = _VERSION_PATTERN.search(output)
    if not match:
        return None

    major = int(match.group(1))
    if major == 1:
        # Old format: 1.8.0 -> major version 8
        minor = match.group(2)
        return int(minor) if minor else major
    return major


def _run_java_version(java_path: Path) -> str | None:
    """Run `java -version` and return stderr output."""
    try:
        result = subprocess.run(
            [str(java_path), "-version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # java -version outputs to stderr
        return result.stderr or result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError, OSError):
        return None


def _check_java_at(path: Path, platform: Platform) -> JavaInstallation | None:
    """Check if a valid Java installation exists at the given path."""
    java_bin = path / "bin" / platform.java_executable
    if not java_bin.exists():
        return None

    output = _run_java_version(java_bin)
    if not output:
        return None

    major = parse_java_version(output)
    if major is None:
        return None

    is_jdk = (path / "bin" / "javac").exists() or (path / "bin" / "javac.exe").exists()

    return JavaInstallation(
        path=path,
        version_string=output.strip().split("\n")[0],
        major_version=major,
        is_jdk=is_jdk,
    )


def _candidate_paths(platform: Platform) -> list[Path]:
    """Generate candidate Java installation paths to search."""
    candidates: list[Path] = []

    # JAVA_HOME
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        candidates.append(Path(java_home))

    # Platform-specific locations
    if platform.os == platform.os.MACOS:
        # macOS: /Library/Java/JavaVirtualMachines/*/Contents/Home
        jvm_dir = Path("/Library/Java/JavaVirtualMachines")
        if jvm_dir.exists():
            for entry in sorted(jvm_dir.iterdir(), reverse=True):
                home = entry / "Contents" / "Home"
                if home.exists():
                    candidates.append(home)

        # Homebrew
        for brew_prefix in ("/opt/homebrew/opt", "/usr/local/opt"):
            brew = Path(brew_prefix)
            if brew.exists():
                for entry in sorted(brew.iterdir(), reverse=True):
                    if "openjdk" in entry.name or "java" in entry.name:
                        candidates.append(entry)
                        libexec = entry / "libexec" / "openjdk.jdk" / "Contents" / "Home"
                        if libexec.exists():
                            candidates.append(libexec)

    elif platform.os == platform.os.LINUX:
        # Linux: /usr/lib/jvm/*
        jvm_dir = Path("/usr/lib/jvm")
        if jvm_dir.exists():
            for entry in sorted(jvm_dir.iterdir(), reverse=True):
                if entry.is_dir():
                    candidates.append(entry)

    elif platform.os == platform.os.WINDOWS:
        # Windows: C:\Program Files\Java\*, C:\Program Files\Eclipse Adoptium\*
        for base in ("C:\\Program Files\\Java", "C:\\Program Files\\Eclipse Adoptium"):
            base_path = Path(base)
            if base_path.exists():
                for entry in sorted(base_path.iterdir(), reverse=True):
                    candidates.append(entry)

    return candidates


def detect_java(
    platform: Platform | None = None,
    min_version: int | None = None,
) -> list[JavaInstallation]:
    """Detect all Java installations on the system.

    Args:
        platform: Target platform (auto-detected if None).
        min_version: Only return installations >= this major version.

    Returns:
        List of found JavaInstallation, sorted by version descending.
    """
    platform = platform or Platform.detect()
    found: list[JavaInstallation] = []
    seen_paths: set[Path] = set()

    for candidate in _candidate_paths(platform):
        resolved = candidate.resolve()
        if resolved in seen_paths:
            continue
        seen_paths.add(resolved)

        inst = _check_java_at(candidate, platform)
        if inst is None:
            continue
        if min_version and inst.major_version < min_version:
            continue
        found.append(inst)

    found.sort(key=lambda j: j.major_version, reverse=True)
    return found


def find_compatible_java(
    required_version: int,
    platform: Platform | None = None,
) -> JavaInstallation | None:
    """Find the best compatible Java installation.

    Args:
        required_version: Minimum JDK major version.
        platform: Target platform.

    Returns:
        Best matching JavaInstallation, or None.
    """
    installations = detect_java(platform=platform, min_version=required_version)
    # Prefer JDK over JRE
    jdks = [j for j in installations if j.is_jdk]
    return jdks[0] if jdks else (installations[0] if installations else None)
