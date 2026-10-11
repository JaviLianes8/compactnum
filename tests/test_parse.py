from decimal import Decimal

import pytest

from compactnum import CompactError, parse, parse_decimal


def test_parses_each_scale() -> None:
    assert parse("1.2k") == 1200
    assert parse("3.5M") == 3_500_000
    assert parse("2B") == 2_000_000_000
    assert parse("1.5T") == 1_500_000_000_000


def test_parses_plain_numbers() -> None:
    assert parse("42") == 42
    assert parse("0") == 0
    assert parse("1200") == 1200


def test_integral_results_are_int_and_others_are_float() -> None:
    assert isinstance(parse("1.2k"), int)
    assert parse("1.2345k") == 1234.5
    assert isinstance(parse("1.2345k"), float)


def test_units_are_case_insensitive() -> None:
    assert parse("1.2K") == 1200
    assert parse("3.5m") == 3_500_000


def test_parses_metric_and_short_scale_letters() -> None:
    assert parse("1.5G") == 1_500_000_000
    assert parse("1.5B") == 1_500_000_000
    assert parse("2Qa") == 2_000_000_000_000_000


def test_parses_binary_prefixes() -> None:
    assert parse("1Ki") == 1024
    assert parse("1.5Ki") == 1536
    assert parse("1mi") == 1024 * 1024
    assert parse("1 gibi") == 1024**3


def test_parses_long_words_and_spacing() -> None:
    assert parse("1.2 thousand") == 1200
    assert parse("2 million") == 2_000_000
    assert parse("  3B  ") == 3_000_000_000


def test_parses_negatives_and_explicit_sign() -> None:
    assert parse("-1.2k") == -1200
    assert parse("+2M") == 2_000_000


def test_unit_is_stripped_before_parsing() -> None:
    assert parse("1.5KiB", unit="B") == 1536
    assert parse("2kB", unit="B") == 2000
    assert parse("900B", unit="B") == 900


def test_missing_expected_unit_is_an_error() -> None:
    with pytest.raises(CompactError):
        parse("1.5Ki", unit="B")


def test_custom_decimal_separator() -> None:
    assert parse("1,5k", decimal_sep=",") == 1500
    with pytest.raises(CompactError):
        parse("1.5k", decimal_sep=",")


def test_parse_decimal_is_exact() -> None:
    assert parse_decimal("1.2k") == Decimal("1200")
    assert parse_decimal("1.5KiB", unit="B") == Decimal("1536")
    big = parse_decimal("999999999999999999k")
    assert big == Decimal("999999999999999999000")
    assert isinstance(big, Decimal)


@pytest.mark.parametrize("bad", ["", "abc", "1.2x", "1.2.3", "1,200", "k", "1 2k"])
def test_rejects_invalid_notation(bad: str) -> None:
    with pytest.raises(CompactError):
        parse(bad)


def test_rejects_non_strings() -> None:
    with pytest.raises(CompactError):
        parse(1200)  # type: ignore[arg-type]


def test_rejects_bad_decimal_separator() -> None:
    with pytest.raises(ValueError):
        parse("1.2k", decimal_sep="99")
