"""Tests for Ghidra version to JDK requirement mapping."""

from __future__ import annotations

from ghidractl.ghidra.version_map import is_jdk_compatible, recommended_jdk, required_jdk


class TestRequiredJdk:
    """Test required_jdk mapping."""

    def test_ghidra_11_3_requires_jdk_21(self) -> None:
        assert required_jdk("11.3") == 21

    def test_ghidra_11_0_requires_jdk_21(self) -> None:
        assert required_jdk("11.0") == 21

    def test_ghidra_10_4_requires_jdk_17(self) -> None:
        assert required_jdk("10.4") == 17

    def test_ghidra_10_0_requires_jdk_17(self) -> None:
        assert required_jdk("10.0") == 17

    def test_ghidra_9_2_requires_jdk_11(self) -> None:
        assert required_jdk("9.2") == 11

    def test_unknown_version_returns_default(self) -> None:
        assert required_jdk("invalid") == 21

    def test_future_version(self) -> None:
        assert required_jdk("12.0") == 21


class TestRecommendedJdk:
    """Test recommended_jdk."""

    def test_no_version_returns_21(self) -> None:
        assert recommended_jdk() == 21

    def test_with_version_delegates(self) -> None:
        assert recommended_jdk("10.4") == 17


class TestIsJdkCompatible:
    """Test compatibility check."""

    def test_jdk_21_with_ghidra_11(self) -> None:
        assert is_jdk_compatible(21, "11.3") is True

    def test_jdk_17_with_ghidra_11(self) -> None:
        assert is_jdk_compatible(17, "11.3") is False

    def test_jdk_21_with_ghidra_10(self) -> None:
        assert is_jdk_compatible(21, "10.4") is True

    def test_jdk_17_with_ghidra_10(self) -> None:
        assert is_jdk_compatible(17, "10.4") is True

    def test_jdk_11_with_ghidra_10(self) -> None:
        assert is_jdk_compatible(11, "10.4") is False
