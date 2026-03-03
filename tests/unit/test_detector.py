"""Tests for Java installation detection."""

from __future__ import annotations

import pytest

from ghidractl.java.detector import parse_java_version


class TestParseJavaVersion:
    """Test java -version output parsing."""

    def test_java_21(self) -> None:
        output = 'openjdk version "21.0.5" 2024-10-15'
        assert parse_java_version(output) == 21

    def test_java_17(self) -> None:
        output = 'openjdk version "17.0.9" 2023-10-17'
        assert parse_java_version(output) == 17

    def test_java_11(self) -> None:
        output = 'openjdk version "11.0.21" 2023-10-17'
        assert parse_java_version(output) == 11

    def test_java_8_old_format(self) -> None:
        output = 'java version "1.8.0_392"'
        assert parse_java_version(output) == 8

    def test_java_9(self) -> None:
        output = 'openjdk version "9.0.4"'
        assert parse_java_version(output) == 9

    def test_no_version(self) -> None:
        assert parse_java_version("no version here") is None

    def test_empty_string(self) -> None:
        assert parse_java_version("") is None

    def test_graalvm_format(self) -> None:
        output = 'openjdk version "21.0.1" 2023-10-17\nOpenJDK Runtime Environment GraalVM CE'
        assert parse_java_version(output) == 21
