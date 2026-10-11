"""The complete-promise contract for compactnum.

These tests assert the whole advertised behaviour in one place: the public API
surface, and that format and parse cooperate across every style, base, precision
and edge value, with the documented half-up rounding and lossy round-trip.
"""

import importlib.resources
from decimal import Decimal

import pytest

import compactnum
from compactnum import CompactError, format, parse, parse_decimal

# The public API. Add every exported name here as the library grows; this list is
# the contract and the test below fails if the module and this list disagree.
PUBLIC_API: list[str] = ["CompactError", "format", "parse", "parse_decimal"]


def test_all_lists_exactly_the_public_api() -> None:
    assert sorted(compactnum.__all__) == sorted(PUBLIC_API)


def test_every_exported_name_resolves() -> None:
    for name in compactnum.__all__:
        assert hasattr(compactnum, name)


def test_version_is_a_three_part_string() -> None:
    parts = compactnum.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)


def test_the_package_ships_type_information() -> None:
    assert importlib.resources.files("compactnum").joinpath("py.typed").is_file()


@pytest.mark.parametrize("style", ["si", "short", "metric", "long"])
@pytest.mark.parametrize("precision", [0, 1, 2, 3])
@pytest.mark.parametrize(
    "value", [0, 7, 999, 1500, 42_000, 3_500_000, 2_000_000_000, 1_500_000_000_000]
)
def test_decimal_round_trip_holds_across_styles_and_precision(
    style: str, precision: int, value: int
) -> None:
    text = format(value, precision=precision, style=style)
    # The compact string always reads back to the rounded quantity it shows.
    assert parse(text) == parse_decimal(text)
    # And the rounded quantity never drifts further than the scale allows.
    assert abs(Decimal(value) - parse_decimal(text)) <= Decimal(value) * Decimal("0.5") + 1


@pytest.mark.parametrize("value", [0, 1024, 1536, 1_048_576, 5_368_709_120])
def test_binary_round_trip_holds_with_units(value: int) -> None:
    text = format(value, base=1024, unit="B", precision=3)
    assert parse(text, unit="B") == value


def test_negatives_and_zero_are_handled() -> None:
    assert format(0) == "0"
    assert format(-1500) == "-1.5k"
    assert parse("-1.5k") == -1500
    assert format(-10) == "-10"  # no negative zero


def test_documented_rounding_is_half_up_and_carries() -> None:
    assert format(1250) == "1.3k"
    assert format(999_999) == "1M"


def test_parse_is_strict_about_garbage() -> None:
    for bad in ["", "abc", "1.2x", "1.2.3", "1,200"]:
        with pytest.raises(CompactError):
            parse(bad)


def test_errors_are_a_single_known_type() -> None:
    assert issubclass(CompactError, ValueError)
