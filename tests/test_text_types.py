"""Text and flag arguments: str subclasses read by value, strict bools, caseless units."""

from __future__ import annotations

import enum
import time
from typing import SupportsIndex

import pytest

from compactnum import CompactError, format, parse, parse_decimal


class Style(str, enum.Enum):
    SHORT = "short"
    METRIC = "metric"


class Sep(str, enum.Enum):
    COMMA = ","


class Unit(str, enum.Enum):
    BYTE = "B"


class Loud(str):
    """A str subclass whose str() and equality differ from its characters."""

    def __str__(self) -> str:
        return "LOUD"

    def __eq__(self, other: object) -> bool:
        return False

    __hash__ = str.__hash__


def test_string_enum_members_are_read_by_their_value() -> None:
    assert format(1_500_000_000, style=Style.METRIC) == "1.5G"
    assert format(1500, style=Style.SHORT) == "1.5k"
    assert format(1500, decimal_sep=Sep.COMMA) == "1,5k"
    assert parse("1,5k", decimal_sep=Sep.COMMA) == 1500
    assert format(1536, base=1024, unit=Unit.BYTE) == "1.5KiB"
    assert parse("1.5KiB", unit=Unit.BYTE) == 1536
    assert parse_decimal(Loud("1.5KiB"), unit=Unit.BYTE) == 1536


def test_str_subclasses_with_their_own_str_and_eq_are_read_by_value() -> None:
    assert format(1500, style=Loud("short")) == "1.5k"
    assert format(1500, style=Loud("long")) == "1.5 thousand"
    assert format(1500, unit=Loud("B")) == "1.5kB"
    assert format(1500, decimal_sep=Loud(",")) == "1,5k"
    assert parse(Loud("1,5kB"), unit=Loud("b"), decimal_sep=Loud(",")) == 1500
    assert type(format(1500, unit=Loud("B"))) is str
    with pytest.raises(ValueError, match="unknown style"):
        format(1500, style=Loud("fancy"))


class Liar(str):
    """A str subclass whose comparisons, methods and repr all lie about its characters."""

    def __eq__(self, other: object) -> bool:
        return False

    def __ne__(self, other: object) -> bool:
        return False

    __hash__ = str.__hash__

    def strip(self, chars: str | None = None, /) -> str:
        return "1k"

    def replace(self, old: str, new: str, count: SupportsIndex = -1, /) -> str:
        return "9"

    def __repr__(self) -> str:
        return "x" * 100_000


def test_a_separator_whose_comparisons_lie_is_read_by_its_characters() -> None:
    assert format(1500, decimal_sep=Liar(",")) == "1,5k"
    assert parse_decimal("1,5k", decimal_sep=Liar(",")) == 1500
    assert parse("1,5k", decimal_sep=Liar(",")) == 1500


def test_text_whose_methods_lie_is_read_by_its_characters() -> None:
    for reader in (parse, parse_decimal):
        assert reader(Liar(" 2.5k ")) == 2500
        with pytest.raises(CompactError) as info:
            reader(Liar("junk"))
        assert len(str(info.value)) < 80 and "xxx" not in str(info.value)
        with pytest.raises(CompactError) as info:
            reader(Liar("junk" * 1000))
        assert len(str(info.value)) < 120 and "xxx" not in str(info.value)


@pytest.mark.parametrize("flag", ["False", "", None, 0, 1, 1.0])
def test_trim_zeros_must_be_a_bool(flag: object) -> None:
    with pytest.raises(TypeError, match="trim_zeros must be a bool"):
        format(2000, trim_zeros=flag)  # type: ignore[arg-type]
    assert format(2000, trim_zeros=True) == "2k"
    assert format(2000, trim_zeros=False) == "2.0k"


def test_unit_matching_is_caseless_even_when_casefold_changes_length() -> None:
    eszett = chr(0xDF)
    assert parse("1.5kSS", unit=eszett) == 1500
    assert parse("1.5kss", unit=eszett) == 1500
    assert parse("1.5k" + eszett, unit="SS") == 1500
    assert parse_decimal("2 kibi Stra" + eszett + "e", unit="STRASSE") == 2048
    assert parse("1.5KIB", unit="b") == 1536


def test_unit_must_end_on_a_character_boundary() -> None:
    eszett = chr(0xDF)
    with pytest.raises(CompactError, match="missing the unit"):
        parse("1k" + eszett, unit="s")
    with pytest.raises(CompactError, match="missing the unit"):
        parse("1kB", unit="xB")


def test_caseless_unit_matching_stays_linear() -> None:
    eszett = chr(0xDF)
    start = time.perf_counter()
    assert parse_decimal("1k" + eszett * 200_000, unit="ss" * 200_000) == 1000
    with pytest.raises(CompactError):
        parse_decimal("1k" + "s" * 200_000, unit=eszett * 200_001)
    assert time.perf_counter() - start < 2.0
